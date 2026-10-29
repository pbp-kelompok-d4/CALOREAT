import json

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from main.models import Reviews
from main.forms import ReviewsForm

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

    def test_review_page_includes_toast_assets_in_order(self):
        response = self.client.get(reverse("main:show_main"))
        content = response.content.decode()

        self.assertContains(response, 'href="/static/css/toast.css"')
        self.assertContains(response, 'src="/static/js/toast.js"')
        self.assertContains(response, 'src="/static/js/reviews.js"')
        self.assertLess(
            content.index('src="/static/js/toast.js"'),
            content.index('src="/static/js/reviews.js"'),
        )

    def test_review_form_limits_content_to_500_characters(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertContains(response, 'name="content"')
        self.assertContains(response, 'maxlength="500"')

        form = ReviewsForm(data={
            "customer_name": "Test User",
            "star": "★★★★★",
            "content": "x" * 500,
        })
        self.assertTrue(form.is_valid())

        form = ReviewsForm(data={
            "customer_name": "Test User",
            "star": "★★★★★",
            "content": "x" * 501,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)

    def test_review_form_rejects_zero_star_rating(self):
        form = ReviewsForm(data={
            "customer_name": "Test User",
            "star": "☆☆☆☆☆",
            "content": "Review content",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("star", form.errors)

    def test_get_reviews_json(self):
        response = self.client.get(reverse("main:get_reviews_json"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["customer_name"], self.review.customer_name)
        self.assertEqual(data[0]["content"], self.review.content)
        self.assertEqual(data[0]["star"], self.review.star)

    def test_get_reviews_json_filters_by_star(self):
        Reviews.objects.all().delete()
        Reviews.objects.create(
            customer_name="Five Star",
            content="Excellent",
            star="★★★★★",
        )
        Reviews.objects.create(
            customer_name="Three Star",
            content="Good",
            star="★★★☆☆",
        )
        Reviews.objects.create(
            customer_name="One Star",
            content="Needs improvement",
            star="★☆☆☆☆",
        )

        response = self.client.get(
            reverse("main:get_reviews_json"),
            {"star": "★★★☆☆"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["customer_name"], "Three Star")
        self.assertEqual(data[0]["star"], "★★★☆☆")

    def test_get_reviews_json_supports_numeric_star_filter(self):
        Reviews.objects.all().delete()
        Reviews.objects.create(
            customer_name="Four Star",
            content="Very good",
            star="★★★★☆",
        )
        Reviews.objects.create(
            customer_name="Two Star",
            content="Could improve",
            star="★★☆☆☆",
        )

        response = self.client.get(
            reverse("main:get_reviews_json"),
            {"star": "4"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["star"], "★★★★☆")

    def test_get_reviews_json_unknown_star_filter_returns_no_reviews(self):
        response = self.client.get(
            reverse("main:get_reviews_json"),
            {"star": "invalid"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_reviews_json_filters_to_authenticated_users_reviews(self):
        Reviews.objects.all().delete()
        own_review = Reviews.objects.create(
            created_by=self.user,
            customer_name="Test User",
            content="My review",
            star="★★★★☆",
        )
        Reviews.objects.create(
            customer_name="Another User",
            content="Someone else's review",
            star="★★★★★",
        )

        response = self.client.get(
            reverse("main:get_reviews_json"),
            {"mine": "1"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], str(own_review.id))
        self.assertEqual(data[0]["customer_name"], "Test User")

    def test_get_reviews_json_mine_filter_can_combine_with_star_filter(self):
        Reviews.objects.all().delete()
        Reviews.objects.create(
            created_by=self.user,
            customer_name="Test User",
            content="My review",
            star="★★★★☆",
        )
        Reviews.objects.create(
            customer_name="Another User",
            content="Five-star review",
            star="★★★★★",
        )

        response = self.client.get(
            reverse("main:get_reviews_json"),
            {"mine": "true", "star": "4"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["star"], "★★★★☆")

    def test_get_reviews_json_mine_filter_returns_no_reviews_for_anonymous_users(self):
        self.client.logout()
        response = self.client.get(
            reverse("main:get_reviews_json"),
            {"mine": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_review_page_shows_mine_filter_only_to_authenticated_users(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertContains(response, 'data-mine="1"')

        self.client.logout()
        response = self.client.get(reverse("main:show_main"))
        self.assertNotContains(response, 'data-mine="1"')

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

    def test_user_cannot_add_more_than_one_review(self):
        Reviews.objects.filter(created_by=self.user).delete()
        Reviews.objects.create(
            created_by=self.user,
            customer_name="Test User",
            content="Existing review",
            star="★★★★★",
        )

        response = self.client.post(
            reverse("main:add_review_ajax"),
            {
                "customer_name": "Test User",
                "star": "★★★★☆",
                "content": "Second review",
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["status"], "error")
        self.assertIn("already have a review", response.json()["message"])
        self.assertEqual(Reviews.objects.filter(created_by=self.user).count(), 1)

    def test_add_review_uses_admin_when_user_has_no_first_name(self):
        self.user.first_name = ""
        self.user.save()

        payload = {
            "customer_name": "Admin",
            "star": "★★★★★",
            "content": "Aplikasi sangat membantu!",
        }
        response = self.client.post(reverse("main:add_review_ajax"), payload)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Reviews.objects.filter(customer_name="Admin").exists())

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

    def test_bulk_delete_reviews_as_superuser(self):
        reviews = Reviews.objects.bulk_create([
            Reviews(customer_name="Bulk One", content="First", star="★★★★★"),
            Reviews(customer_name="Bulk Two", content="Second", star="★★★★☆"),
        ])

        response = self.client.post(
            reverse("main:bulk_delete_reviews_ajax"),
            {"ids": [str(review.id) for review in reviews]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(response.json()["deleted_count"], 2)
        self.assertFalse(Reviews.objects.filter(id__in=[review.id for review in reviews]).exists())

    def test_bulk_delete_reviews_accepts_json_ids(self):
        reviews = Reviews.objects.bulk_create([
            Reviews(customer_name="JSON One", content="First", star="★★★★★"),
            Reviews(customer_name="JSON Two", content="Second", star="★★★☆☆"),
        ])

        response = self.client.post(
            reverse("main:bulk_delete_reviews_ajax"),
            data=json.dumps({"ids": [str(review.id) for review in reviews]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["deleted_count"], 2)

    def test_bulk_delete_reviews_rejects_empty_selection(self):
        response = self.client.post(
            reverse("main:bulk_delete_reviews_ajax"),
            {"ids": []},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "No reviews selected for deletion.")

    def test_bulk_delete_reviews_rejects_invalid_ids(self):
        response = self.client.post(
            reverse("main:bulk_delete_reviews_ajax"),
            data=json.dumps({"ids": ["not-a-uuid"]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Invalid review ID.")

    def test_non_superuser_cannot_bulk_delete_reviews(self):
        regular_user = User.objects.create_user(
            username="bulk-regular@example.com",
            is_superuser=False,
        )
        self.client.force_login(regular_user)

        response = self.client.post(
            reverse("main:bulk_delete_reviews_ajax"),
            {"ids": [str(self.review.id)]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Reviews.objects.filter(id=self.review.id).exists())

    def test_review_creator_can_edit_and_delete_review(self):
        owner = User.objects.create_user(
            username="owner@example.com",
            password="owner-password",
            first_name="Review Owner",
        )
        review = Reviews.objects.create(
            created_by=owner,
            customer_name="Review Owner",
            content="Original review",
            star="★★★★★",
        )
        self.client.force_login(owner)

        edit_response = self.client.post(
            reverse("main:edit_review", kwargs={"reviews_id": review.id}),
            {
                "customer_name": "Review Owner",
                "star": "★★★★☆",
                "content": "Updated review",
            },
        )
        self.assertEqual(edit_response.status_code, 200)
        review.refresh_from_db()
        self.assertEqual(review.content, "Updated review")

        delete_response = self.client.post(
            reverse("main:delete_review_ajax", kwargs={"id": review.id})
        )
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(Reviews.objects.filter(id=review.id).exists())

    def test_non_creator_cannot_edit_review(self):
        owner = User.objects.create_user(
            username="owner@example.com",
            password="owner-password",
        )
        other_user = User.objects.create_user(
            username="other@example.com",
            password="other-password",
        )
        review = Reviews.objects.create(
            created_by=owner,
            customer_name="Review Owner",
            content="Original review",
            star="★★★★★",
        )
        self.client.force_login(other_user)

        response = self.client.post(
            reverse("main:edit_review", kwargs={"reviews_id": review.id}),
            {
                "customer_name": "Other User",
                "star": "★☆☆☆☆",
                "content": "Unauthorized edit",
            },
        )
        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.content, "Original review")

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