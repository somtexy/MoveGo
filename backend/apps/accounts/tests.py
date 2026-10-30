
import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class AuthTests(TestCase):

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.refresh_csrf_token()

    def refresh_csrf_token(self):
        response = self.client.get("/api/auth/csrf/")
        self.token = response.json()["csrfToken"]

    def post(self, url, data, csrf=True):
        headers = (
            {"HTTP_X_CSRFTOKEN": self.token}
            if csrf else {}
        )

        return self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
            **headers
        )

    def test_registration_login_profile_logout(self):
        data = {
            "email": "TEST@example.com",
            "password": "Strong_Password_782!",
            "first_name": "Ada",
            "role": "passenger"
        }

        # Register user
        response = self.post("/api/auth/register/", data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json()["user"]["email"],
            "test@example.com"
        )

        # Check authenticated profile
        self.assertEqual(
            self.client.get("/api/auth/me/").status_code,
            200
        )

        # Registration logged the user in and rotated CSRF
        self.refresh_csrf_token()

        # Logout
        self.assertEqual(
            self.post("/api/auth/logout/", {}).status_code,
            200
        )

        # Profile should no longer be accessible
        self.assertEqual(
            self.client.get("/api/auth/me/").status_code,
            401
        )

        # Login again
        self.assertEqual(
            self.post(
                "/api/auth/login/",
                {
                    "email": "test@example.com",
                    "password": data["password"]
                }
            ).status_code,
            200
        )

        # Login rotated CSRF again
        self.refresh_csrf_token()

        # Duplicate registration should fail
        self.assertEqual(
            self.post("/api/auth/register/", data).status_code,
            409
        )

    def test_csrf_is_required(self):
        response = self.post(
            "/api/auth/register/",
            {
                "email": "a@example.com",
                "first_name": "A",
                "password": "Strongpass_9892!"
            },
            csrf=False
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            get_user_model().objects.count(),
            0
        )

    def test_password_validation_and_bad_login(self):
        result = self.post(
            "/api/auth/register/",
            {
                "email": "a@example.com",
                "first_name": "A",
                "password": "123"
            }
        )

        self.assertEqual(result.status_code, 400)

        result = self.post(
            "/api/auth/login/",
            {
                "email": "no@example.com",
                "password": "wrong"
            }
        )

        self.assertEqual(result.status_code, 401)
