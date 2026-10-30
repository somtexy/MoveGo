"""Step 43 trip lifecycle permission and transition tests."""
import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.accounts.models import RiderProfile
from apps.drivers.models import DriverProfile
from .models import Ride

class TripLifecycleTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.passenger = User.objects.create_user(username='trip43passenger', password='TestABC123!')
        self.driver = User.objects.create_user(username='trip43driver', password='TestABC123!')
        self.other = User.objects.create_user(username='trip43other', password='TestABC123!')
        RiderProfile.objects.create(user=self.passenger, phone='+2348000043001', phone_verified=True, role=RiderProfile.Role.PASSENGER)
        RiderProfile.objects.create(user=self.driver, phone='+2348000043002', phone_verified=True, role=RiderProfile.Role.DRIVER)
        RiderProfile.objects.create(user=self.other, phone='+2348000043003', phone_verified=True, role=RiderProfile.Role.PASSENGER)
        self.ride = Ride.objects.create(passenger=self.passenger,driver=self.driver,pickup_label='Pickup',destination_label='Destination',category='Ride',status=Ride.Status.ASSIGNED,estimated_fare_kobo=120000)
        self.url=f'/api/trips/{self.ride.pk}/advance/'
    def advance(self,action):
        return self.client.post(self.url,json.dumps({'action':action}),content_type='application/json')
    def test_driver_can_complete_ordered_lifecycle(self):
        self.client.force_login(self.driver)
        for action,status in [('depart',Ride.Status.ARRIVING),('arrive',Ride.Status.ARRIVED),('start',Ride.Status.STARTED),('complete',Ride.Status.COMPLETED)]:
            res=self.advance(action)
            self.assertEqual(res.status_code,200,res.content)
            self.ride.refresh_from_db()
            self.assertEqual(self.ride.status,status)
        self.assertEqual(self.advance('complete').status_code,409)
    def test_cannot_skip_or_repeat_transition(self):
        self.client.force_login(self.driver)
        self.assertEqual(self.advance('complete').status_code,409)
        self.assertEqual(self.advance('depart').status_code,200)
        self.assertEqual(self.advance('depart').status_code,409)
    def test_passenger_cannot_advance(self):
        self.client.force_login(self.passenger)
        self.assertEqual(self.advance('depart').status_code,403)
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.status,Ride.Status.ASSIGNED)
    def test_other_user_cannot_access_trip(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'/api/trips/{self.ride.pk}/').status_code,404)
        self.assertEqual(self.advance('depart').status_code,403)
    def test_my_trip_view_is_party_scoped(self):
        for user,visible in [(self.passenger,True),(self.driver,True),(self.other,False)]:
            self.client.force_login(user)
            response=self.client.get('/api/trips/my/')
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['ride'] is not None,visible)
    def test_cancelled_and_unassigned_cannot_progress(self):
        self.client.force_login(self.driver)
        Ride.objects.filter(pk=self.ride.pk).update(status=Ride.Status.CANCELLED)
        self.assertEqual(self.advance('depart').status_code,409)
    def test_csrf_enforced(self):
        from django.test import Client
        c=Client(enforce_csrf_checks=True)
        c.force_login(self.driver)
        self.assertEqual(c.post(self.url,json.dumps({'action':'depart'}),content_type='application/json').status_code,403)
