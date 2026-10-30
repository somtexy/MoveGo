import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import RiderProfile
from .pin_models import AppPIN

class PINTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(username='pin-user',password='some-password')
        RiderProfile.objects.create(user=self.user,phone='+2348012345678',phone_verified=True)
        self.client.force_login(self.user)
    def post(self,name,**data):
        return self.client.post('/api/auth/pin/'+name+'/',data=json.dumps(data),content_type='application/json')
    def test_setup_and_verify(self):
        self.assertEqual(self.post('setup',pin='123456',confirm='123456').status_code,201)
        self.assertNotEqual(AppPIN.objects.get(user=self.user).encoded_pin,'123456')
        self.assertEqual(self.post('verify',pin='123456').status_code,200)
    def test_duplicate_and_change(self):
        self.post('setup',pin='123456',confirm='123456')
        self.assertEqual(self.post('setup',pin='999999',confirm='999999').status_code,409)
        self.assertEqual(self.post('change',old_pin='123456',new_pin='445566',confirm='445566').status_code,200)
        self.assertEqual(self.post('verify',pin='445566').status_code,200)
    def test_lockout(self):
        self.post('setup',pin='123456',confirm='123456')
        for _ in range(5): self.post('verify',pin='000000')
        self.assertEqual(self.post('verify',pin='123456').status_code,429)
    def test_requires_phone_and_login(self):
        self.user.movego_profile.phone_verified=False;self.user.movego_profile.save()
        self.assertEqual(self.post('setup',pin='123456',confirm='123456').status_code,403)
        self.client.logout()
        self.assertEqual(self.post('setup',pin='123456',confirm='123456').status_code,401)
    def test_recovery_is_not_session_only(self):
        self.assertEqual(self.post('recover').status_code,501)
