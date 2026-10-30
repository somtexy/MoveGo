"""Offline Twilio adapter tests: no outbound messages or real credentials."""
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
from django.test import TestCase
from .models import PhoneOTP, RiderProfile

PHONE = "+2348030000000"  # Fictional test number; nothing sent.


class TwilioVerifyTests(TestCase):
    def post(self, path, data):
        return self.client.post(path, data=json.dumps(data), content_type="application/json")

    @patch("apps.accounts.twilio_verify.twilio_service")
    def test_send_check_and_session(self, factory):
        service = Mock()
        service.verifications.create.return_value = SimpleNamespace(status="pending")
        service.verification_checks.create.return_value = SimpleNamespace(status="approved")
        factory.return_value = service
        self.assertEqual(self.post("/api/auth/phone/twilio/request/", {"phone": PHONE}).status_code, 200)
        service.verifications.create.assert_called_once_with(to=PHONE, channel="sms")
        self.assertEqual(self.post("/api/auth/phone/twilio/check/", {"phone": PHONE, "code": "123456"}).status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertTrue(RiderProfile.objects.get(phone=PHONE).phone_verified)
        self.assertEqual(self.post("/api/auth/phone/twilio/check/", {"phone": PHONE, "code": "123456"}).status_code, 400)

    @patch("apps.accounts.twilio_verify.twilio_service")
    def test_cooldown_and_invalid_code(self, factory):
        service = Mock()
        service.verifications.create.return_value = SimpleNamespace(status="pending")
        service.verification_checks.create.return_value = SimpleNamespace(status="pending")
        factory.return_value = service
        self.assertEqual(self.post("/api/auth/phone/twilio/request/", {"phone": PHONE}).status_code, 200)
        self.assertEqual(self.post("/api/auth/phone/twilio/request/", {"phone": PHONE}).status_code, 429)
        self.assertEqual(self.post("/api/auth/phone/twilio/check/", {"phone": PHONE, "code": "111111"}).status_code, 400)
        self.assertEqual(PhoneOTP.objects.get(phone=PHONE).attempts, 1)

    @patch("apps.accounts.twilio_verify.twilio_service", side_effect=RuntimeError("Not configured"))
    def test_missing_credentials(self, factory):
        self.assertEqual(self.post("/api/auth/phone/twilio/request/", {"phone": PHONE}).status_code, 503)
        self.assertFalse(PhoneOTP.objects.exists())
