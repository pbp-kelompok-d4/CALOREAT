from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from main.models import Reviews

# Create your tests here.
class MainTest(TestCase):
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

    def test_review_page(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertContains(response, 'id="reviewCardsContainer"')

    def test_get_reviews_json(self):
        response = self.client.get(reverse("main:get_reviews_json"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["customer_name"], self.review.customer_name)
        self.assertEqual(data[0]["content"], self.review.content)
        self.assertEqual(data[0]["star"], self.review.star)

    def test_empty_review_page(self):
        Reviews.objects.all().delete()
        response = self.client.get(reverse("main:get_reviews_json"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, [])

    def test_add_review_ajax_success(self):
        payload = {
            "customer_name": "Fachri",
            "star": "★★★★★",
            "content": "Aplikasi sangat membantu!",
        }
        response = self.client.post(reverse("main:add_review_ajax"), payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "success")
        self.assertTrue(Reviews.objects.filter(customer_name="Test User").exists())

    def test_add_review_ajax_invalid(self):
        # customer_name kosong
        payload = {
            "customer_name": "",
            "star": "★★★★★",
            "content": "Aplikasi sangat membantu!",
        }
        response = self.client.post(reverse("main:add_review_ajax"), payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")

    def test_delete_review_ajax_success(self):
        review_id = self.review.id
        response = self.client.post(reverse("main:delete_review_ajax", kwargs={"id": review_id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertFalse(Reviews.objects.filter(id=review_id).exists())

    def test_delete_review_ajax_not_found(self):
        import uuid
        fake_id = uuid.uuid4()
        response = self.client.post(reverse("main:delete_review_ajax", kwargs={"id": fake_id}))
        self.assertEqual(response.status_code, 404)

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