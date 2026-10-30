from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from apps.accounts.models import RiderProfile
from apps.drivers.models import DriverProfile,DriverLocation
from .models import Ride

class DiscoveryTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.p=User.objects.create_user(username='discovery-passenger',password='pass123ABC!')
        RiderProfile.objects.create(user=self.p,phone='+2348000001001',phone_verified=True,role=RiderProfile.Role.PASSENGER)
        self.other=User.objects.create_user(username='another-passenger',password='pass123ABC!')
        RiderProfile.objects.create(user=self.other,phone='+2348000001002',phone_verified=True,role=RiderProfile.Role.PASSENGER)
        self.ride=Ride.objects.create(passenger=self.p,pickup_label='Abuja pickup',destination_label='Abuja destination',pickup_latitude=9.0765,pickup_longitude=7.3986,destination_latitude=9.09,destination_longitude=7.42,category='Ride',estimated_fare_kobo=250000,status=Ride.Status.REQUESTED)
        self.url=f'/api/driver-discovery/nearby/?ride_id={self.ride.pk}'
    def driver(self,idx,lat=9.078,lon=7.399,approved=True,online=True,verified=True,accuracy=15,old=False):
        u=get_user_model().objects.create_user(username=f'discovery-driver-{idx}',password='pass123ABC!')
        RiderProfile.objects.create(user=u,phone=f'+2348000002{idx:03}',phone_verified=verified,role=RiderProfile.Role.DRIVER)
        d=DriverProfile.objects.create(user=u,full_name='Test Driver',license_number=f'TEST-{idx}',vehicle_make='Toyota',vehicle_model='Corolla',vehicle_color='Black',plate_number=f'ABC{idx}',review_status=DriverProfile.Review.APPROVED if approved else DriverProfile.Review.PENDING,is_online=online)
        loc=DriverLocation.objects.create(driver=d,latitude=lat,longitude=lon,accuracy_m=accuracy)
        if old:DriverLocation.objects.filter(pk=loc.pk).update(updated_at=timezone.now()-timedelta(minutes=3))
    def test_auth_and_ride_ownership(self):
        self.assertEqual(self.client.get(self.url).status_code,401)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).status_code,404)
    def test_no_driver_details_are_exposed(self):
        self.client.force_login(self.p);self.driver(1)
        result=self.client.get(self.url)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['availability'],'few')
        self.assertNotIn('drivers',result.json())
        self.assertNotIn('latitude',str(result.json()))
        self.assertFalse(result.json()['dispatch_available'])
    def test_excludes_unqualified_locations(self):
        self.client.force_login(self.p)
        self.driver(1,approved=False);self.driver(2,online=False);self.driver(3,verified=False)
        self.driver(4,accuracy=500);self.driver(5,old=True);self.driver(6,lat=10,lon=8)
        self.assertEqual(self.client.get(self.url).json()['availability'],'none')
    def test_several_and_completed_protected(self):
        self.client.force_login(self.p)
        for idx in range(1,5):self.driver(idx)
        self.assertEqual(self.client.get(self.url).json()['availability'],'several')
        self.ride.status=Ride.Status.CANCELLED;self.ride.save(update_fields=['status'])
        self.assertEqual(self.client.get(self.url).status_code,409)
    def test_reject_arbitrary_coordinates(self):
        self.client.force_login(self.p)
        self.assertEqual(self.client.get('/api/driver-discovery/nearby/?lat=9&lon=7').status_code,400)
