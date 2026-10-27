from datetime import date
import json
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse

from main.calorie_views import _needs, _summary
from main.models import CalorieProfile, FoodEntry
from main.off import normalize, OpenFoodFactsError


class OpenFoodFactsNormalizationTests(TestCase):
    def test_normalizes_complete_product(self):
        product = normalize({
            "code": "12345678", "product_name": "Oat Drink", "brands": "Brand A, Brand B",
            "image_front_small_url": "https://example.test/oat.jpg", "serving_quantity": "200",
            "nutriscore_grade": "b", "nutriments": {
                "energy-kcal_100g": "45", "proteins_100g": "1.2",
                "carbohydrates_100g": "6.8", "fat_100g": "1.4",
            },
        })
        self.assertEqual(product["name"], "Oat Drink")
        self.assertEqual(product["brand"], "Brand A")
        self.assertEqual(product["kcal_100g"], 45)
        self.assertEqual(product["serving_g"], 200)
        self.assertEqual(product["nutriscore"], "b")
        self.assertTrue(product["has_nutrition"])

    def test_uses_kilojoule_fallback(self):
        product = normalize({"product_name": "Energy only", "nutriments": {"energy-kj_100g": "418.4"}})
        self.assertEqual(product["kcal_100g"], 100)

    def test_missing_or_bad_nutrition_stays_missing(self):
        without_data = normalize({"product_name": "Unknown food", "nutriments": {}})
        bad_data = normalize({"product_name": "Bad values", "nutriments": {"energy-kcal_100g": "unknown"}})
        self.assertIsNone(without_data["kcal_100g"])
        self.assertFalse(without_data["has_nutrition"])
        self.assertIsNone(bad_data["kcal_100g"])

    def test_products_without_names_are_skipped(self):
        self.assertIsNone(normalize({"brands": "Brand", "nutriments": {"energy-kcal_100g": 200}}))

    def test_saved_open_food_facts_fixtures_cover_edge_cases(self):
        fixture_path = Path(__file__).parent / "fixtures" / "off_products.json"
        fixtures = json.loads(fixture_path.read_text())
        normalized = [normalize(product) for product in fixtures]
        self.assertEqual(len(fixtures), 4)
        self.assertEqual(normalized[0]["kcal_100g"], 42.4)
        self.assertEqual(normalized[1]["kcal_100g"], 300)
        self.assertFalse(normalized[2]["has_nutrition"])
        self.assertIsNone(normalized[3])


class CaloriePageTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="rina@example.test", password="Passw0rd!", first_name="Rina")
        self.client.force_login(self.user)

    def test_anonymous_page_redirects_back_after_login(self):
        self.client.logout()
        response = self.client.get(reverse("main:calorie_count"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("next=/calorie-count/", response.url)

    def test_login_returns_to_next_page(self):
        self.client.logout()
        response = self.client.post(reverse("main:login"), {
            "username": "rina@example.test", "password": "Passw0rd!", "remember_me": "on",
            "next": reverse("main:calorie_count"),
        })
        self.assertRedirects(response, reverse("main:calorie_count"), fetch_redirect_response=False)

    def test_profile_needs_calculation_and_floor(self):
        profile = CalorieProfile.objects.create(
            user=self.user, sex="female", birth_date=date(2000, 1, 1), height_cm=150,
            weight_kg=42, activity_level="sedentary", goal="lose_05",
        )
        needs = _needs(profile, date(2026, 10, 22))
        self.assertTrue(needs["complete"])
        self.assertEqual(needs["goal_kcal"], 1200)

    def test_authenticated_page_renders_dashboard_regions(self):
        response = self.client.get(reverse("main:calorie_count"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="summary-region"')
        self.assertContains(response, 'id="food-search-form"')
        self.assertContains(response, 'id="meals-region"')
        self.assertContains(response, 'id="week-region"')
        self.assertContains(response, 'id="needs-region"')
        self.assertContains(response, 'id="manual-entry-launch"')

    def test_profile_endpoint_saves_profile_and_computes_target(self):
        payload = {
            "sex": "female", "birth_date": "2005-10-22", "height_cm": 165,
            "weight_kg": 58, "activity_level": "light", "goal": "maintain",
        }
        response = self.client.put(reverse("main:profile"), payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["complete"])
        self.assertEqual(response.json()["goal_kcal"], 1850)

    def test_profile_goal_and_macro_targets(self):
        profile = CalorieProfile.objects.create(
            user=self.user, sex="female", birth_date=date(2005, 10, 22), height_cm=165,
            weight_kg=58, activity_level="light", goal="maintain",
        )
        needs = _needs(profile, date(2026, 10, 22))
        self.assertEqual(needs["bmr"], 1345)
        self.assertEqual(needs["maintenance"], 1850)

    def test_summary_uses_only_users_entries_and_scales_macros(self):
        CalorieProfile.objects.create(
            user=self.user, sex="female", birth_date=date(2005, 10, 22), height_cm=165,
            weight_kg=58, activity_level="light", goal="maintain",
        )
        other = User.objects.create_user(username="other@example.test", password="Passw0rd!")
        FoodEntry.objects.create(user=self.user, date=date(2026, 10, 22), meal="lunch", name="Rice", grams=200,
                                 kcal_100g=150, protein_100g=3, carbs_100g=28, fat_100g=2)
        FoodEntry.objects.create(user=other, date=date(2026, 10, 22), meal="lunch", name="Other", grams=100,
                                 kcal_100g=900)
        result = _summary(self.user, date(2026, 10, 22))
        self.assertEqual(result["consumed_kcal"], 300)
        self.assertEqual(result["remaining_kcal"], 1550)
        self.assertEqual(result["macros"]["carbs"]["consumed_g"], 56)

    def test_other_users_entry_is_404(self):
        other = User.objects.create_user(username="other@example.test", password="Passw0rd!")
        entry = FoodEntry.objects.create(user=other, date=date(2026, 10, 22), meal="lunch", name="Private food", grams=100, kcal_100g=100)
        response = self.client.delete(reverse("main:entry_detail", args=[entry.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(FoodEntry.objects.filter(pk=entry.pk).exists())

    def test_search_too_short(self):
        response = self.client.get(reverse("main:foods_search"), {"q": "a"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "query_too_short")

    def test_search_throttle_returns_429(self):
        with patch("main.calorie_views.search_products", return_value=[]):
            first = self.client.get(reverse("main:foods_search"), {"q": "rice"})
            second = self.client.get(reverse("main:foods_search"), {"q": "bread"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.json()["error"], "slow_down")

    def test_global_search_limit_is_shared_across_users(self):
        with patch("main.calorie_views.search_products", return_value=[]):
            statuses = []
            for index in range(11):
                user = User.objects.create_user(username=f"search-{index}@example.test", password="Passw0rd!")
                self.client.force_login(user)
                response = self.client.get(reverse("main:foods_search"), {"q": f"query {index}"})
                statuses.append(response.status_code)
        self.assertEqual(statuses[:10], [200] * 10)
        self.assertEqual(statuses[10], 429)

    def test_future_date_is_rejected_and_week_has_seven_days(self):
        tomorrow = (timezone.localdate() + timedelta(days=1)).isoformat()
        rejected = self.client.get(reverse("main:summary"), {"date": tomorrow})
        self.assertEqual(rejected.status_code, 400)
        week = self.client.get(reverse("main:summary_week"))
        self.assertEqual(week.status_code, 200)
        self.assertEqual(len(week.json()["days"]), 7)

    def test_upstream_failure_returns_502(self):
        with patch("main.calorie_views.search_products", side_effect=OpenFoodFactsError()):
            response = self.client.get(reverse("main:foods_search"), {"q": "rice"})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["error"], "upstream_unavailable")

    def test_upstream_rate_limit_returns_429(self):
        with patch("main.calorie_views.search_products", side_effect=OpenFoodFactsError(429)):
            response = self.client.get(reverse("main:foods_search"), {"q": "rice"})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"], "slow_down")

    def test_entry_create_validates_range_and_returns_summary(self):
        CalorieProfile.objects.create(
            user=self.user,
            sex="female",
            birth_date=date(2000, 1, 1),
            height_cm=160,
            weight_kg=55,
            activity_level="moderate",
            goal="maintain",
        )

        payload = {
            "date": "2026-10-22", "meal": "lunch", "name": "Rice", "grams": 250,
            "kcal_100g": 152, "protein_100g": 4.1, "carbs_100g": 24, "fat_100g": 4.5,
        }
        response = self.client.post(reverse("main:entries"), payload, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["entry"]["kcal"], 380)
        self.assertIn("summary", response.json())
        payload["grams"] = 5001
        invalid = self.client.post(reverse("main:entries"), payload, content_type="application/json")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.json()["error"], "invalid_grams")
