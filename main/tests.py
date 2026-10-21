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
