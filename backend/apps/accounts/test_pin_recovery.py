import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase
from .models import RiderProfile
from .pin_models import AppPIN

class RecoveryTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(username='recovery-user',password='not-the-pin')
        RiderProfile.objects.create(user=self.user,phone='+2348030000000',phone_verified=True)
        AppPIN.objects.create(user=self.user,encoded_pin=make_password('123456'))
        self.client.force_login(self.user)
    def post(self,stage,**data):
        return self.client.post('/api/auth/pin/recovery/'+stage+'/',data=json.dumps(data),content_type='application/json')
    @patch('apps.accounts.pin_recovery.twilio_service')
    def test_fresh_sms_required_and_one_time_reset(self,service_factory):
        service=Mock()
        service.verifications.create.return_value=SimpleNamespace(status='pending')
        service.verification_checks.create.return_value=SimpleNamespace(status='approved')
        service_factory.return_value=service
        self.assertEqual(self.post('reset',pin='654321',confirm='654321').status_code,403)
        self.assertEqual(self.post('request').status_code,200)
        self.assertEqual(self.post('confirm',code='123456').status_code,200)
        self.assertEqual(self.post('reset',pin='654321',confirm='654321').status_code,200)
        self.assertTrue(check_password('654321',AppPIN.objects.get(user=self.user).encoded_pin))
        self.assertEqual(self.post('reset',pin='111111',confirm='111111').status_code,403)
    @patch('apps.accounts.pin_recovery.twilio_service')
    def test_wrong_code_and_sms_rate_limit(self,service_factory):
        service=Mock()
        service.verifications.create.return_value=SimpleNamespace(status='pending')
        service.verification_checks.create.return_value=SimpleNamespace(status='pending')
        service_factory.return_value=service
        self.assertEqual(self.post('request').status_code,200)
        self.assertEqual(self.post('request').status_code,429)
        self.assertEqual(self.post('confirm',code='999999').status_code,400)
        self.assertEqual(self.post('reset',pin='654321',confirm='654321').status_code,403)
    def test_no_anonymous_reset(self):
        self.client.logout()
        self.assertEqual(self.post('request').status_code,401)
        self.assertEqual(self.post('reset',pin='654321',confirm='654321').status_code,401)
