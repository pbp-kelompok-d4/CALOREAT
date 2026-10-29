import json

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from main.models import Reviews
from main.forms import ReviewsForm

# Create your tests here.
class ReviewsTest(TestCase):
    # URL TEST
    def test_main_url_is_exist(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_main_named_url_is_exist(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")

    def test_nonexistent_url_returns_404(self):
        response = self.client.get("/nonexistent-page-12345/")
        self.assertEqual(response.status_code, 404)
    def setUp(self):
        self.user = User.objects.create_user(
            username="test@example.com",
            password="test-password-123",
            is_superuser=True,
            first_name="Test User",
        )
        self.client.login(username="test@example.com", password="test-password-123")
        self.review = Reviews.objects.create(
            customer_name="Roko Rido",
            content="Logging meals takes seconds. Love it.",
            star="★★★★★",
        )

    def test_review_model(self):
        self.assertEqual(str(self.review), "Roko Rido")
        self.assertEqual(self.review.star, "★★★★★")
        self.assertEqual(self.review.content, "Logging meals takes seconds. Love it.")
        
    # Navbar test
    def test_navbar_renders_all_links_and_mobile_drawer(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "header.html")
        self.assertContains(response, reverse("main:show_main"))
        self.assertContains(response, reverse("main:food_catalog"))
        self.assertContains(response, reverse("main:calorie_count"))
        self.assertContains(response, reverse("main:portion_guidance"))
        self.assertContains(response, 'id="nav-toggle"')
        self.assertContains(response, 'id="nav-icon4"')
        self.assertContains(response, 'id="nav-mobile-drawer"')

    def test_navbar_authenticated_state_shows_user_and_logout(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertContains(response, "Test User")
        self.assertContains(response, reverse("main:logout"))
        self.assertNotContains(response, 'class="nav-actions')
        self.assertNotContains(response, 'class="life-highlight__signup"')

    def test_navbar_anonymous_state_shows_login_and_signup(self):
        self.client.logout()
        response = self.client.get(reverse("main:show_main"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("main:login"))
        self.assertContains(response, reverse("main:register"))
        self.assertContains(response, 'class="life-highlight__signup"')
        self.assertNotContains(response, "Log out")

    def test_main_page_search_form_points_to_food_catalog(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertContains(response, f'action="{reverse("main:food_catalog")}"')
        self.assertContains(response, 'name="q"')
        self.assertContains(response, "js/food_search.js")

    def test_feature_dashboard_links_to_feature_pages(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertContains(response, f'href="{reverse("main:calorie_count")}"')
        self.assertContains(response, f'href="{reverse("main:portion_guidance")}"')
        self.assertContains(response, f'href="{reverse("main:food_catalog")}"')
        self.assertContains(response, "Daily Calorie & Macro Tracker")
        self.assertContains(response, "Smart Portion Guidance")
        self.assertContains(response, "Curated Food & Nutrient Explorer")
        self.assertNotContains(response, "this is feature")

    def test_non_superuser_cannot_delete_review(self):
        regular_user = User.objects.create_user(
            username="regular@example.com",
            password="test-password-123",
            is_superuser=False,
        )
        self.client.force_login(regular_user)
        response = self.client.post(
            reverse("main:delete_review_ajax", kwargs={"id": self.review.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Reviews.objects.filter(id=self.review.id).exists())

    def test_navbar_marks_home_link_active_on_main_page(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertContains(
            response,
            f'href="{reverse("main:show_main")}" class="hover:text-ink active font-bold text-ink" aria-current="page"',
        )

    def test_register_view_get_and_post_and_duplicate_email(self):
        self.client.logout()
        get_response = self.client.get(reverse("main:register"))
        self.assertEqual(get_response.status_code, 200)

        post_response = self.client.post(
            reverse("main:register"),
            {
                "full_name": "New User",
                "email": "newuser@example.com",
                "password": "StrongPassword123!",
            },
        )
        self.assertRedirects(post_response, reverse("main:login"))
        self.assertTrue(User.objects.filter(username="newuser@example.com").exists())

        duplicate_response = self.client.post(
            reverse("main:register"),
            {
                "full_name": "Duplicate User",
                "email": "newuser@example.com",
                "password": "StrongPassword123!",
            },
        )
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertContains(duplicate_response, "Email ini sudah terdaftar.")

    def test_login_and_logout_views(self):
        self.client.logout()
        get_response = self.client.get(reverse("main:login"))
        self.assertEqual(get_response.status_code, 200)

        login_response = self.client.post(
            reverse("main:login"),
            {
                "username": "test@example.com",
                "password": "test-password-123",
            },
        )
        self.assertRedirects(login_response, reverse("main:show_main"))

        logout_response = self.client.post(reverse("main:logout"))
        self.assertRedirects(logout_response, reverse("main:login"))

        next_login_response = self.client.post(
            reverse("main:login"),
            {
                "username": "test@example.com",
                "password": "test-password-123",
                "remember_me": "on",
                "next": reverse("main:food_catalog"),
            },
        )
        self.assertRedirects(next_login_response, reverse("main:food_catalog"))
