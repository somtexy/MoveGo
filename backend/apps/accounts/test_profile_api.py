import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import RiderProfile


class ProfileAPITests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="phone_2348000000001", password=None)
        self.user.set_unusable_password()
        self.user.save(update_fields=["password"])
        RiderProfile.objects.create(user=self.user, phone="+2348000000001", phone_verified=True)

    def patch(self, data):
        return self.client.patch("/api/auth/profile/", data=json.dumps(data), content_type="application/json")

    def test_requires_login(self):
        self.assertEqual(self.client.get("/api/auth/profile/").status_code, 401)
        self.assertEqual(self.patch({}).status_code, 401)

    def test_save_then_read(self):
        self.client.force_login(self.user)
        response = self.patch({"first_name": "Ada", "last_name": "Okafor", "email": "ada@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["profile"]["phone"], "+2348000000001")
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.json()["profile"]["first_name"], "Ada")
        self.assertEqual(response.json()["profile"]["email"], "ada@example.com")

    def test_validation_and_duplicate_email(self):
        User = get_user_model()
        User.objects.create_user(username="other", email="taken@example.com", password="strongPassword!123")
        self.client.force_login(self.user)
        self.assertEqual(self.patch({"first_name": "A", "last_name": "", "email": ""}).status_code, 400)
        self.assertEqual(self.patch({"first_name": "Ada", "last_name": "", "email": "taken@example.com"}).status_code, 409)

    def test_csrf_protected(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.user)
        response = c.patch("/api/auth/profile/", data=json.dumps({"first_name":"Ada", "last_name":"", "email":""}), content_type="application/json")
        self.assertEqual(response.status_code, 403)
