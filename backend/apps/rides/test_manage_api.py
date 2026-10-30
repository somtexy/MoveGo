import json
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from apps.accounts.models import RiderProfile
from .models import Ride

class RideManagementTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.user=User.objects.create_user(username='cancel40',password='TestPass!123')
        self.other=User.objects.create_user(username='cancel40b',password='TestPass!123')
        self.driver=User.objects.create_user(username='cancel40d',password='TestPass!123')
        for user,role,num in [(self.user,'passenger','+2348011111111'),(self.other,'passenger','+2348022222222'),(self.driver,'driver','+2348033333333')]:
            RiderProfile.objects.create(user=user, role=role, phone=num,phone_verified=True)
        self.ride=Ride.objects.create(passenger=self.user, pickup_label='Wuse',destination_label='Maitama',category='Ride')
        self.client=Client(enforce_csrf_checks=True)
        self.client.get('/api/auth/csrf/')
        self.csrf=self.client.cookies['csrftoken'].value

    def cancel(self,id=None,csrf=True):
        return self.client.post(f'/api/ride-management/{id or self.ride.pk}/cancel/',data='{}',content_type='application/json',**({'HTTP_X_CSRFTOKEN':self.csrf} if csrf else {}))

    def test_anonymous_and_driver_denied(self):
        self.assertEqual(self.client.get('/api/ride-management/active/').status_code,401)
        self.assertEqual(self.cancel().status_code,401)
        self.client.force_login(self.driver)
        self.assertEqual(self.client.get('/api/ride-management/active/').status_code,403)
        self.assertEqual(self.cancel().status_code,403)

    def test_csrf_enforced(self):
        self.client.force_login(self.user)
        self.assertEqual(self.cancel(csrf=False).status_code,403)
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.status,Ride.Status.REQUESTED)

    def test_cancel_requested_and_repeat(self):
        self.client.force_login(self.user)
        self.assertTrue(self.client.get('/api/ride-management/active/').json()['ride']['can_cancel'])
        self.assertEqual(self.cancel().status_code,200)
        self.assertEqual(self.cancel().status_code,200)
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.status,Ride.Status.CANCELLED)
        self.assertIsNone(self.client.get('/api/ride-management/active/').json()['ride'])

    def test_not_other_passengers(self):
        self.client.force_login(self.other)
        self.assertEqual(self.cancel().status_code,404)

    def test_started_and_assigned_protected(self):
        self.client.force_login(self.user)
        self.ride.status=Ride.Status.STARTED
        self.ride.save(update_fields=['status'])
        self.assertEqual(self.cancel().status_code,409)
        self.ride.status=Ride.Status.ASSIGNED
        self.ride.driver=self.driver
        self.ride.save(update_fields=['status','driver'])
        self.assertEqual(self.cancel().status_code,409)
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.status,Ride.Status.ASSIGNED)

    def test_bad_payload_and_completed_protected(self):
        self.client.force_login(self.user)
        response=self.client.post(f'/api/ride-management/{self.ride.pk}/cancel/',data=json.dumps({'status':'cancelled'}),content_type='application/json',HTTP_X_CSRFTOKEN=self.csrf)
        self.assertEqual(response.status_code,400)
        self.ride.status=Ride.Status.COMPLETED
        self.ride.save(update_fields=['status'])
        self.assertEqual(self.cancel().status_code,409)
