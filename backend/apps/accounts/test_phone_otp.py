import json
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from .models import PhoneOTP, RiderProfile
from .otp import digest

@override_settings(DEBUG=True, MOVEGO_OTP_DEV_CONSOLE=True)
class PhoneOTPTests(TestCase):
    def setUp(self):
        self.client.get("/api/auth/csrf/")

    def post(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    @patch("apps.accounts.otp.send_code")
    def test_issue_verify_one_time_and_session(self, send):
        self.assertEqual(self.post("/api/auth/phone/request-otp/", {"phone":"07070985813"}).status_code, 200)
        self.assertEqual(send.call_count, 1)
        phone, code = send.call_args.args
        self.assertEqual(phone, "+2347070985813")
        self.assertEqual(self.post("/api/auth/phone/verify-otp/", {"phone":phone, "code":code}).status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertEqual(RiderProfile.objects.get(phone=phone).phone_verified, True)
        self.assertEqual(self.post("/api/auth/phone/verify-otp/", {"phone":phone, "code":code}).status_code, 400)

    @patch("apps.accounts.otp.send_code")
    def test_limits_invalid_code_and_expiry(self, send):
        phone = "+2347070985813"
        self.post("/api/auth/phone/request-otp/", {"phone":phone})
        self.assertEqual(self.post("/api/auth/phone/request-otp/", {"phone":phone}).status_code, 429)
        for _ in range(5):
            self.assertEqual(self.post("/api/auth/phone/verify-otp/", {"phone":phone, "code":"9999"}).status_code, 400)
        code = send.call_args.args[1]
        self.assertEqual(self.post("/api/auth/phone/verify-otp/", {"phone":phone, "code":code}).status_code, 400)
        row = PhoneOTP.objects.get(phone=phone)
        row.code_digest = digest(phone, "1234")
        row.attempts = 0
        row.expires_at = timezone.now() - timedelta(seconds=1)
        row.save()
        self.assertEqual(self.post("/api/auth/phone/verify-otp/", {"phone":phone, "code":"1234"}).status_code, 400)

    @override_settings(MOVEGO_OTP_DEV_CONSOLE=False)
    def test_disabled_delivery(self):
        self.assertEqual(self.post("/api/auth/phone/request-otp/", {"phone":"07070985813"}).status_code, 503)
        self.assertFalse(PhoneOTP.objects.exists())
