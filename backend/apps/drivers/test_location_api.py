import json
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone
from apps.accounts.models import RiderProfile
from .models import DriverProfile, DriverLocation

class DriverLocationAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='gps-driver', password='testing-pass-123')
        self.rp = RiderProfile.objects.create(user=self.user, phone='+2348000000949', phone_verified=True, role=RiderProfile.Role.DRIVER)
        self.profile = DriverProfile.objects.create(user=self.user, full_name='Ada Driver', license_number='TEST-1234', vehicle_make='Toyota', vehicle_model='Corolla', vehicle_color='White', plate_number='ABC123XY')
        self.client = Client(enforce_csrf_checks=True)
        self.client.get('/api/auth/csrf/')
        self.csrf = self.client.cookies['csrftoken'].value

    def send(self, endpoint='/api/drivers/location/', value=None, csrf=True):
        return self.client.post(endpoint, data=json.dumps(value if value is not None else {'lat':9.075,'lon':7.492,'accuracy_m':25}), content_type='application/json', **({'HTTP_X_CSRFTOKEN':self.csrf} if csrf else {}))

    def online(self):
        self.profile.review_status = DriverProfile.Review.APPROVED
        self.profile.is_online = True
        self.profile.save()

    def test_requires_login_approval_and_online(self):
        self.assertEqual(self.send().status_code, 401)
        self.client.force_login(self.user)
        self.assertEqual(self.send().status_code, 403)
        self.online()
        self.assertEqual(self.send().status_code, 200)
        self.assertEqual(DriverLocation.objects.count(), 1)

    def test_csrf_required(self):
        self.client.force_login(self.user); self.online()
        self.assertEqual(self.send(csrf=False).status_code, 403)
        self.assertFalse(DriverLocation.objects.exists())

    def test_validation(self):
        self.client.force_login(self.user); self.online()
        for payload in ({'lat':91,'lon':7,'accuracy_m':1}, {'lat':True,'lon':7,'accuracy_m':1}, {'lat':9,'lon':7,'accuracy_m':-1}, {'lat':9,'lon':7}, {'lat':'NaN','lon':7,'accuracy_m':1}):
            self.assertEqual(self.send(value=payload).status_code,400)
        self.assertFalse(DriverLocation.objects.exists())

    def test_upsert_and_stale(self):
        self.client.force_login(self.user); self.online()
        self.assertEqual(self.send().status_code,200)
        self.assertEqual(self.send(value={'lat':9.08,'lon':7.49,'accuracy_m':10}).status_code,200)
        self.assertEqual(DriverLocation.objects.count(),1)
        response=self.client.get('/api/drivers/location/status/')
        self.assertTrue(response.json()['fresh'])
        self.assertNotIn('latitude', response.json())
        DriverLocation.objects.update(updated_at=timezone.now()-timedelta(minutes=5))
        self.assertFalse(self.client.get('/api/drivers/location/status/').json()['fresh'])

    def test_offline_erases_location(self):
        self.client.force_login(self.user); self.online();self.send()
        response=self.send('/api/drivers/availability/', {'is_online':False})
        self.assertEqual(response.status_code,200)
        self.assertFalse(DriverLocation.objects.exists())
        self.assertEqual(self.send().status_code,403)

    def test_stop_deletes_location_even_when_offline(self):
        self.client.force_login(self.user); self.online();self.send()
        self.profile.is_online=False;self.profile.save()
        response=self.send('/api/drivers/location/stop/',{})
        self.assertEqual(response.status_code,200)
        self.assertFalse(DriverLocation.objects.exists())
