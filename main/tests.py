from django.test import TestCase
from django.urls import reverse

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

    #Review model test
    def setUp(self):
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
        self.assertContains(response, self.review.customer_name)
        self.assertContains(response, self.review.content)
        self.assertContains(response, self.review.star)

    def test_empty_review_page(self):
        Reviews.objects.all().delete()
        response = self.client.get(reverse("main:show_main"))
        self.assertContains(response, "There are no reviews yet, add some!")