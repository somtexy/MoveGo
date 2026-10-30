import json
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.utils import timezone
from apps.accounts.models import RiderProfile
from apps.drivers.models import DriverProfile, DriverLocation
from .models import Ride
from .offer_models import RideOffer

class DispatchTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.p=User.objects.create_user(username='step42passenger',password='TestABC123!')
        RiderProfile.objects.create(user=self.p,phone='+2348001000001',phone_verified=True,role=RiderProfile.Role.PASSENGER)
        self.other=User.objects.create_user(username='step42other',password='TestABC123!')
        RiderProfile.objects.create(user=self.other,phone='+2348001000002',phone_verified=True,role=RiderProfile.Role.PASSENGER)
        self.ride=Ride.objects.create(passenger=self.p,pickup_label='Abuja pickup',destination_label='Abuja drop',pickup_latitude=9.0765,pickup_longitude=7.3986,category='Ride',status=Ride.Status.REQUESTED,estimated_fare_kobo=120000)
        self.url=f'/api/dispatch/rides/{self.ride.pk}/offer/'
    def create_driver(self,idx,*,online=True,approved=True,accuracy=10,old=False,lat=9.077):
        u=get_user_model().objects.create_user(username=f'step42driver{idx}',password='TestABC123!')
        RiderProfile.objects.create(user=u,phone=f'+2348001001{idx:03}',phone_verified=True,role=RiderProfile.Role.DRIVER)
        d=DriverProfile.objects.create(user=u,full_name='Driver',license_number=f'A{idx}',vehicle_make='Toyota',vehicle_model='Corolla',vehicle_color='Black',plate_number=f'ABC{idx}',review_status=DriverProfile.Review.APPROVED if approved else DriverProfile.Review.PENDING,is_online=online)
        loc=DriverLocation.objects.create(driver=d,latitude=lat,longitude=7.399,accuracy_m=accuracy)
        if old: DriverLocation.objects.filter(pk=loc.pk).update(updated_at=timezone.now()-timedelta(minutes=5))
        return u
    def post(self,url,data): return self.client.post(url,json.dumps(data),content_type='application/json')
    def test_passenger_only_and_ownership(self):
        self.assertEqual(self.post(self.url,{}).status_code,401)
        self.client.force_login(self.other);self.assertEqual(self.post(self.url,{}).status_code,404)
        self.assertEqual(self.client.get('/api/dispatch/driver/offer/').status_code,403)
    def test_filters_and_no_private_driver_details(self):
        self.create_driver(1,online=False);self.create_driver(2,accuracy=400);self.create_driver(3,old=True)
        self.client.force_login(self.p)
        self.assertEqual(self.post(self.url,{}).json()['state'],'no_driver')
        u=self.create_driver(4)
        r=self.post(self.url,{})
        self.assertEqual(r.status_code,201)
        self.assertEqual(r.json()['state'],'offered')
        self.assertNotIn(str(u.username),str(r.json()))
        self.assertNotIn('latitude',str(r.json()))
        self.assertEqual(RideOffer.objects.count(),1)
    def test_accept_and_repeat_rejected(self):
        u=self.create_driver(1)
        self.client.force_login(self.p);self.assertEqual(self.post(self.url,{}).status_code,201)
        offer=RideOffer.objects.get()
        self.client.force_login(u)
        self.assertEqual(self.client.get('/api/dispatch/driver/offer/').json()['offer']['offer_id'],offer.pk)
        url=f'/api/dispatch/driver/offers/{offer.pk}/respond/'
        self.assertEqual(self.post(url,{'action':'accept'}).status_code,200)
        self.ride.refresh_from_db();self.assertEqual(self.ride.driver_id,u.id)
        self.assertEqual(self.ride.status,Ride.Status.ASSIGNED)
        self.assertEqual(self.post(url,{'action':'accept'}).status_code,409)
    def test_decline_then_other_driver(self):
        first=self.create_driver(1,lat=9.0766);second=self.create_driver(2,lat=9.078)
        self.client.force_login(self.p);self.post(self.url,{})
        offer=RideOffer.objects.get();self.assertEqual(offer.driver_id,first.pk)
        self.client.force_login(first);self.assertEqual(self.post(f'/api/dispatch/driver/offers/{offer.pk}/respond/',{'action':'decline'}).status_code,200)
        self.client.force_login(self.p);self.assertEqual(self.post(self.url,{}).status_code,201)
        self.assertEqual(RideOffer.objects.filter(status='pending').get().driver_id,second.pk)
    def test_expiry_and_cancellation_prevent_claim(self):
        first=self.create_driver(1);self.client.force_login(self.p);self.post(self.url,{})
        offer=RideOffer.objects.get()
        RideOffer.objects.filter(pk=offer.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.client.force_login(first)
        self.assertEqual(self.post(f'/api/dispatch/driver/offers/{offer.pk}/respond/',{'action':'accept'}).status_code,409)
        self.client.force_login(self.p)
        self.post(f'/api/ride-management/{self.ride.pk}/cancel/',{})
        self.client.force_login(first)
        self.assertEqual(self.post(f'/api/dispatch/driver/offers/{offer.pk}/respond/',{'action':'accept'}).status_code,409)
        self.ride.refresh_from_db();self.assertIsNone(self.ride.driver_id)
