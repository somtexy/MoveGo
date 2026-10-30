import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from apps.accounts.models import RiderProfile
from .models import Ride

URL = "/api/ride-requests/"
PAYLOAD = {
    "pickup": {"label": "Wuse 2, Abuja", "lat": 9.076, "lon": 7.483},
    "destination": {"label": "Gwarinpa, Abuja", "lat": 9.112, "lon": 7.415},
    "category": "Ride", "payment_method": "cash",
}


class RideRequestTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="request33", password="Password!44881")
        RiderProfile.objects.create(user=self.user, role="passenger", phone="+2348111111199", phone_verified=True)
        self.client = Client(enforce_csrf_checks=True)
        self.client.get("/api/auth/csrf/")
        self.token = self.client.cookies["csrftoken"].value

    def submit(self, payload=None, csrf=True):
        return self.client.post(URL, data=json.dumps(PAYLOAD if payload is None else payload),
                                content_type="application/json", **({"HTTP_X_CSRFTOKEN": self.token} if csrf else {}))

    def test_authentication_required(self):
        self.assertEqual(self.submit().status_code, 401)

    def test_csrf_protection(self):
        self.client.force_login(self.user)
        self.assertEqual(self.submit(csrf=False).status_code, 403)

    def test_reject_online_payment_and_bad_coordinates(self):
        self.client.force_login(self.user)
        self.assertEqual(self.submit({**PAYLOAD, "payment_method": "paystack"}).status_code, 422)
        self.assertEqual(self.submit({**PAYLOAD, "destination": PAYLOAD["pickup"]}).status_code, 400)
        self.assertEqual(Ride.objects.count(), 0)

    @patch("apps.rides.request_api._fetch")
    def test_server_calculates_and_saves_once(self, fetch):
        self.client.force_login(self.user)
        fetch.return_value = ({"results": [{"distance": 8000, "time": 1200}]}, None)
        result = self.submit()
        self.assertEqual(result.status_code, 201)
        ride = Ride.objects.get(pk=result.json()["ride_id"])
        self.assertEqual(ride.status, Ride.Status.REQUESTED)
        self.assertEqual(ride.estimated_fare_kobo, 326000)
        self.assertIsNone(ride.driver)
        self.assertEqual(result.json()["dispatch_status"], "unavailable")
        self.assertEqual(self.submit().status_code, 409)
        self.assertEqual(Ride.objects.count(), 1)

    @patch("apps.rides.request_api._fetch")
    def test_provider_failure_creates_no_ride(self, fetch):
        from django.http import JsonResponse
        self.client.force_login(self.user)
        fetch.return_value = (None, JsonResponse({"error": "Provider down"}, status=502))
        self.assertEqual(self.submit().status_code, 502)
        self.assertEqual(Ride.objects.count(), 0)
