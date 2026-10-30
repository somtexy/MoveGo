import json
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.utils import timezone
from .models import RiderProfile
from .pin_models import AppPIN
from .pin_guard import SESSION_KEY

class SensitivePINTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(username='sensitive-user', password='some-password', email='old@example.com')
        RiderProfile.objects.create(user=self.user,phone='+2348012345678',phone_verified=True)
        AppPIN.objects.create(user=self.user,encoded_pin=make_password('123456'))
        self.client.force_login(self.user)

    def patch_email(self, email='new@example.com', first_name='Ada'):
        return self.client.patch('/api/auth/profile/', data=json.dumps({'first_name':first_name,'last_name':'','email':email}),content_type='application/json')

    def verify(self, pin='123456'):
        return self.client.post('/api/auth/pin/verify/',data=json.dumps({'pin':pin}),content_type='application/json')

    def test_email_change_requires_recent_pin(self):
        self.assertEqual(self.patch_email().status_code,403)
        self.user.refresh_from_db();self.assertEqual(self.user.email,'old@example.com')
        self.assertEqual(self.verify().status_code,200)
        self.assertEqual(self.patch_email().status_code,200)

    def test_name_update_does_not_require_pin(self):
        self.assertEqual(self.patch_email(email='old@example.com',first_name='Amina').status_code,200)

    def test_expired_confirmation_is_rejected(self):
        self.verify()
        s=self.client.session
        v=s[SESSION_KEY];v['at']-=301;s[SESSION_KEY]=v;s.save()
        self.assertEqual(self.patch_email().status_code,403)

    def test_change_pin_revokes_prior_confirmation(self):
        self.verify()
        response=self.client.post('/api/auth/pin/change/',data=json.dumps({'old_pin':'123456','new_pin':'654321','confirm':'654321'}),content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.patch_email().status_code,403)

    def test_other_user_session_has_no_pin_confirmation(self):
        self.verify()
        self.client.logout()
        other=get_user_model().objects.create_user(username='different-user',password='password2')
        RiderProfile.objects.create(user=other,phone='+2348099999999',phone_verified=True)
        AppPIN.objects.create(user=other,encoded_pin=make_password('123456'))
        self.client.force_login(other)
        self.assertEqual(self.patch_email().status_code,403)
