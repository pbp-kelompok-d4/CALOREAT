import uuid

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from main.models import DEFAULT_PROFILE_PICTURE, Reviews


class ReviewAPITest(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin@example.com",
            password="test-password",
            email="admin@example.com",
            first_name="AdminUser",
        )
        self.creator = User.objects.create_user(
            username="creator@example.com",
            password="test-password",
            first_name="Budi",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            password="test-password",
            first_name="Siti",
        )
        self.review = Reviews.objects.create(
            created_by=self.creator,
            customer_name="Budi",
            star="★★★★☆",
            content="Helpful calorie tracker.",
        )
        self.list_url = reverse("api:review-list")
        self.detail_url = reverse("api:review-detail", args=[self.review.id])
        self.payload = {
            "star": "★★★★★",
            "content": "Super accurate and easy to use.",
        }

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.review.id))
        self.assertEqual(response.data[0]["customer_name"], "Budi")
        self.assertFalse(response.data[0]["can_edit"])
        self.assertFalse(response.data[0]["can_delete"])
        self.assertNotIn("created_by", response.data[0])

        self.assertEqual(self.client.head(self.list_url).status_code, status.HTTP_200_OK)
        detail_response = self.client.get(self.detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["id"], str(self.review.id))
        self.assertEqual(self.client.head(self.detail_url).status_code, status.HTTP_200_OK)

    def test_list_filters_by_star_and_mine(self):
        Reviews.objects.create(
            created_by=self.other_user,
            customer_name="Siti",
            star="★★☆☆☆",
            content="Needs more local dishes.",
        )

        self.assertEqual(len(self.client.get(self.list_url, {"star": "4"}).data), 1)
        self.assertEqual(len(self.client.get(self.list_url, {"star": "★★☆☆☆"}).data), 1)
        self.assertEqual(self.client.get(self.list_url, {"star": "invalid"}).data, [])
        self.assertEqual(self.client.get(self.list_url, {"mine": "1"}).data, [])

        self.client.force_authenticate(user=self.creator)
        mine_only = self.client.get(self.list_url, {"mine": "1"})
        self.assertEqual(len(mine_only.data), 1)
        self.assertEqual(mine_only.data[0]["id"], str(self.review.id))

        combined = self.client.get(self.list_url, {"mine": "true", "star": "4"})
        self.assertEqual(len(combined.data), 1)
        self.assertEqual(self.client.get(self.list_url, {"mine": "1", "star": "2"}).data, [])

    def test_missing_review_returns_404(self):
        url = reverse("api:review-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_cannot_write(self):
        self.assertEqual(
            self.client.post(self.list_url, self.payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.put(self.detail_url, self.payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.patch(self.detail_url, {"star": "★☆☆☆☆"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(self.detail_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(Reviews.objects.count(), 1)

    def test_superuser_permissions_create_edit_and_delete(self):
        self.client.force_authenticate(user=self.superuser)

        detail_data = self.client.get(self.detail_url).data
        self.assertFalse(detail_data["can_edit"])
        self.assertTrue(detail_data["can_delete"])

        # Rule 3: Only non-superusers can create new reviews
        self.assertEqual(
            self.client.post(self.list_url, self.payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        # Rule 2: Superuser cannot edit someone else's review
        self.assertEqual(
            self.client.patch(self.detail_url, {"star": "★☆☆☆☆"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.put(self.detail_url, self.payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.review.refresh_from_db()
        self.assertEqual(self.review.star, "★★★★☆")

        # Rule 1: Superuser can delete any review
        delete_response = self.client.delete(self.detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Reviews.objects.filter(pk=self.review.id).exists())

    def test_non_superuser_can_create_and_duplicate_returns_409(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            self.list_url,
            {"star": "★★★★★", "content": "<b>Great</b> app!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["customer_name"], "Siti")
        self.assertEqual(response.data["content"], "Great app!")
        self.assertTrue(response.data["can_edit"])
        self.assertTrue(response.data["can_delete"])

        created = Reviews.objects.get(pk=response.data["id"])
        self.assertEqual(created.created_by, self.other_user)

        duplicate = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Reviews.objects.filter(created_by=self.other_user).count(), 1)

    def test_read_only_fields_cannot_be_forged(self):
        forged_id = str(uuid.uuid4())
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            self.list_url,
            {
                **self.payload,
                "id": forged_id,
                "customer_name": "Forged Name",
                "profile_picture": "https://evil.example.com/pic.png",
                "date": "01 Jan 1999",
                "can_edit": False,
                "can_delete": False,
                "created_by": self.superuser.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data["id"], forged_id)
        self.assertEqual(response.data["customer_name"], "Siti")
        self.assertEqual(response.data["profile_picture"], DEFAULT_PROFILE_PICTURE)
        self.assertTrue(response.data["can_edit"])
        self.assertTrue(response.data["can_delete"])

    def test_validation_rejects_invalid_inputs(self):
        self.client.force_authenticate(user=self.other_user)
        for bad_payload, field in [
            ({"star": "☆☆☆☆☆", "content": "Valid text"}, "star"),
            ({"star": "invalid", "content": "Valid text"}, "star"),
            ({"star": "★★★★★", "content": "   "}, "content"),
            ({"star": "★★★★★", "content": "<p><strong></strong></p>"}, "content"),
            ({"star": "★★★★★", "content": "x" * 501}, "content"),
        ]:
            response = self.client.post(self.list_url, bad_payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)
        self.assertEqual(Reviews.objects.count(), 1)

    def test_only_creator_can_edit_and_delete_own_review(self):
        # Other regular user cannot edit or delete creator's review
        self.client.force_authenticate(user=self.other_user)
        other_view = self.client.get(self.detail_url).data
        self.assertFalse(other_view["can_edit"])
        self.assertFalse(other_view["can_delete"])

        self.assertEqual(
            self.client.put(self.detail_url, self.payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.patch(self.detail_url, {"star": "★☆☆☆☆"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(self.detail_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )

        # Creator can read flags, PATCH, PUT (without altering customer_name), and DELETE
        self.client.force_authenticate(user=self.creator)
        owner_view = self.client.get(self.detail_url).data
        self.assertTrue(owner_view["can_edit"])
        self.assertTrue(owner_view["can_delete"])

        patch_response = self.client.patch(
            self.detail_url, {"star": "★★★★★"}, format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.star, "★★★★★")
        self.assertEqual(self.review.content, "Helpful calorie tracker.")

        incomplete_put = self.client.put(
            self.detail_url, {"star": "★★★☆☆"}, format="json",
        )
        self.assertEqual(incomplete_put.status_code, status.HTTP_400_BAD_REQUEST)

        put_response = self.client.put(
            self.detail_url,
            {
                "star": "★★★☆☆",
                "content": "Updated review text.",
                "customer_name": "Tampered",
            },
            format="json",
        )
        self.assertEqual(put_response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.star, "★★★☆☆")
        self.assertEqual(self.review.content, "Updated review text.")
        self.assertEqual(self.review.customer_name, "Budi")

        delete_response = self.client.delete(self.detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(delete_response.content, b"")
        self.assertFalse(Reviews.objects.filter(pk=self.review.id).exists())

    def test_orphan_review_without_creator_permissions(self):
        orphan = Reviews.objects.create(
            created_by=None,
            customer_name="Legacy",
            star="★★★★★",
            content="Legacy review.",
        )
        orphan_url = reverse("api:review-detail", args=[orphan.id])

        self.client.force_authenticate(user=self.other_user)
        self.assertEqual(
            self.client.patch(orphan_url, {"star": "★☆☆☆☆"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(self.client.delete(orphan_url).status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.superuser)
        self.assertEqual(
            self.client.patch(orphan_url, {"star": "★☆☆☆☆"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(self.client.delete(orphan_url).status_code, status.HTTP_204_NO_CONTENT)

    def test_wrong_method_returns_405(self):
        self.client.force_authenticate(user=self.creator)
        self.assertEqual(
            self.client.delete(self.list_url).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.post(self.detail_url, self.payload, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="other@example.com", password="test-password"))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Reviews.objects.count(), 1)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="other@example.com", password="test-password"))
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value

        create_response = client.post(
            self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        created_url = reverse("api:review-detail", args=[create_response.data["id"]])
        patch_response = client.patch(
            created_url, {"star": "★★★★☆"}, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        delete_response = client.delete(created_url, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
