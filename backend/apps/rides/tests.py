from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import RiderProfile
from .models import Ride


class RideHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.a = User.objects.create_user(username="ride-a", password="SecureTest!248")
        cls.b = User.objects.create_user(username="ride-b", password="SecureTest!248")
        cls.driver = User.objects.create_user(username="ride-driver", password="SecureTest!248")
        RiderProfile.objects.create(user=cls.a, role="passenger", phone="+2348111111111", phone_verified=True)
        RiderProfile.objects.create(user=cls.b, role="passenger", phone="+2348222222222", phone_verified=True)
        RiderProfile.objects.create(user=cls.driver, role="driver", phone="+2348333333333", phone_verified=True)
        cls.ride = Ride.objects.create(passenger=cls.a, pickup_label="A", destination_label="B", category="ride")
        Ride.objects.create(passenger=cls.b, pickup_label="Secret", destination_label="Private", category="comfort")

    def test_anonymous_denied(self):
        self.assertEqual(self.client.get("/api/rides/history/").status_code, 401)

    def test_passenger_sees_only_own_real_rides(self):
        self.client.force_login(self.a)
        response = self.client.get("/api/rides/history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["rides"]), 1)
        self.assertEqual(response.json()["rides"][0]["id"], self.ride.id)
        self.assertIsNone(response.json()["rides"][0]["estimated_fare_kobo"])
        self.assertNotIn("Secret", str(response.json()))

    def test_driver_cannot_access_passenger_history(self):
        self.client.force_login(self.driver)
        self.assertEqual(self.client.get("/api/rides/history/").status_code, 403)

    def test_no_ride_creation_from_client(self):
        self.client.force_login(self.a)
        self.assertEqual(self.client.post("/api/rides/history/", data={}).status_code, 405)
