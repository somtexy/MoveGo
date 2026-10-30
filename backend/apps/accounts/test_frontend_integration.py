
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.conf import settings
from apps.accounts.frontend_dev import FRONTEND_ROOT


@override_settings(
    DEBUG=True,
    ALLOWED_HOSTS=["testserver", "127.0.0.1", "localhost"]
)
class SameOriginFrontendTests(TestCase):

    def test_frontend_and_api_share_origin(self):
         # Test frontend and API routes
        self.assertEqual(
            self.client.get(
                "/app/passenger/account.html"
            ).status_code,
            200
        )

        self.assertEqual(
            self.client.get(
                "/app/js/api-client.js"
            ).status_code,
            200
        )

        self.assertEqual(
            self.client.get("/api/auth/me/").status_code,
            401
        )

    def test_authenticated_session_and_logout(self):
        # Create test user
        user = get_user_model().objects.create_user(
            username="dev@example.com",
            email="dev@example.com",
            password="Secure_Test_883!"
        )

        # Log in the test user
        self.client.force_login(user)

        # Check authenticated profile
        result = self.client.get("/api/auth/me/")

        self.assertEqual(result.status_code, 200)

        self.assertEqual(
            result.json()["user"]["email"],
            "dev@example.com"
        )

        # Log out
        self.assertEqual(
            self.client.post(
                "/api/auth/logout/",
                data="{}",
                content_type="application/json"
            ).status_code,
            200
        )

        # Confirm user is logged out
        self.assertEqual(
            self.client.get("/api/auth/me/").status_code,
            401
        )

    def test_disallowed_asset(self):
        # Prevent access to backend files
        self.assertEqual(
            self.client.get(
                "/app/../backend/config/settings.py"
            ).status_code,
            404
        )
