
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from main.models import PortionGuide


class PortionGuideTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="portion_staff",
            password="TestPass123!",
            is_staff=True,
        )
        self.user = User.objects.create_user(
            username="portion_user",
            password="TestPass123!",
        )

        self.guide = PortionGuide.objects.create(
            title="Balanced Lunch",
            meal_type="lunch",
            description="A balanced meal for lunch.",
            vegetables="Half a plate of vegetables",
            protein="Grilled chicken",
            carbohydrates="Brown rice",
        )

    def test_anonymous_user_is_redirected_from_guidance(self):
        response = self.client.get(reverse("main:portion_guidance"))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_can_view_guidance(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("main:portion_guidance"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "portion_guidance.html")
        self.assertContains(response, "Balanced Lunch")

    def test_guidance_can_be_filtered_by_meal_type(self):
        PortionGuide.objects.create(
            title="Healthy Breakfast",
            meal_type="breakfast",
            description="A balanced breakfast.",
            vegetables="Fruit",
            protein="Eggs",
            carbohydrates="Whole-grain bread",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("main:portion_guidance"),
            {"meal_type": "breakfast"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Healthy Breakfast")
        self.assertNotContains(response, "Balanced Lunch")

    def test_staff_can_create_guide(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("main:portion_create"),
            {
                "title": "Healthy Dinner",
                "meal_type": "dinner",
                "description": "A balanced dinner.",
                "vegetables": "Steamed broccoli",
                "protein": "Fish",
                "carbohydrates": "Potatoes",
                "image_url": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            PortionGuide.objects.filter(title="Healthy Dinner").exists()
        )

    def test_non_staff_cannot_create_guide(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("main:portion_create"),
            {
                "title": "Unauthorized Guide",
                "meal_type": "lunch",
                "description": "Should not be created.",
                "vegetables": "Vegetables",
                "protein": "Tofu",
                "carbohydrates": "Rice",
                "image_url": "",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            PortionGuide.objects.filter(title="Unauthorized Guide").exists()
        )

    def test_staff_can_edit_guide(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse(
                "main:portion_edit",
                kwargs={"guide_id": self.guide.pk},
            ),
            {
                "title": "Updated Lunch",
                "meal_type": "lunch",
                "description": "Updated meal description.",
                "vegetables": "Spinach",
                "protein": "Tempeh",
                "carbohydrates": "Brown rice",
                "image_url": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.guide.refresh_from_db()
        self.assertEqual(self.guide.title, "Updated Lunch")
        self.assertEqual(self.guide.protein, "Tempeh")

    def test_non_staff_cannot_edit_guide(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "main:portion_edit",
                kwargs={"guide_id": self.guide.pk},
            ),
            {
                "title": "Unauthorized Edit",
                "meal_type": "lunch",
                "description": "Should not update.",
                "vegetables": "Vegetables",
                "protein": "Tofu",
                "carbohydrates": "Rice",
                "image_url": "",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.guide.refresh_from_db()
        self.assertEqual(self.guide.title, "Balanced Lunch")

    def test_staff_can_delete_guide(self):
        self.client.force_login(self.staff)
        guide_id = self.guide.pk

        response = self.client.post(
            reverse(
                "main:portion_delete",
                kwargs={"guide_id": guide_id},
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            PortionGuide.objects.filter(pk=guide_id).exists()
        )

    def test_delete_requires_post(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse(
                "main:portion_delete",
                kwargs={"guide_id": self.guide.pk},
            )
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            PortionGuide.objects.filter(pk=self.guide.pk).exists()
        )

    def test_non_staff_cannot_delete_guide(self):
        self.client.force_login(self.user)
        guide_id = self.guide.pk

        response = self.client.post(
            reverse(
                "main:portion_delete",
                kwargs={"guide_id": guide_id},
            )
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            PortionGuide.objects.filter(pk=guide_id).exists()
        )

    
    def test_ajax_request_returns_only_guide_list_partial(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("main:portion_guidance"),
            {"meal_type": "lunch"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "components/portion_guide_list.html",
        )
        self.assertContains(response, "Balanced Lunch")
        self.assertNotContains(response, "Healthy Portion Guidance")

    def test_ajax_filter_returns_matching_guides_only(self):
        PortionGuide.objects.create(
            title="Healthy Breakfast",
            meal_type="breakfast",
            description="A balanced breakfast.",
            vegetables="Fruit",
            protein="Eggs",
            carbohydrates="Whole-grain bread",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("main:portion_guidance"),
            {"meal_type": "breakfast"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Healthy Breakfast")
        self.assertNotContains(response, "Balanced Lunch")

