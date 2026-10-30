import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from .fare_api import quote_amount_kobo

URL = "/api/fares/quotes/"
POINTS = {"pickup": {"lat": 9.07, "lon": 7.49}, "destination": {"lat": 9.10, "lon": 7.53}}


class FareAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="rider31", email="rider31@example.com", password="secure-test-1234"
        )
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.user)

    def post(self, payload, csrf=True):
        if csrf:
            self.client.get("/api/auth/csrf/")
            token = self.client.cookies["csrftoken"].value
            headers = {"HTTP_X_CSRFTOKEN": token}
        else:
            headers = {}
        return self.client.post(URL, data=json.dumps(payload), content_type="application/json", **headers)

    @patch("apps.rides.fare_api._fetch")
    def test_valid_quote_ignores_client_price_and_distance(self, fetch):
        fetch.return_value = ({"results": [{"distance": 10000, "time": 1200}]}, None)
        response = self.post(POINTS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["quotes"]), 4)
        self.assertEqual(data["distance_m"], 10000)
        self.assertGreater(data["quotes"][0]["estimated_fare_kobo"], 0)
        self.assertEqual(self.post({**POINTS, "estimated_fare_kobo": 1}).status_code, 400)

    def test_invalid_coordinates(self):
        self.assertEqual(self.post({"pickup": POINTS["pickup"], "destination": POINTS["pickup"]}).status_code, 400)

    def test_csrf_required(self):
        self.assertEqual(self.post(POINTS, csrf=False).status_code, 403)

    def test_auth_required(self):
        self.client.logout()
        self.assertEqual(self.post(POINTS).status_code, 401)

    def test_rounding(self):
        self.assertEqual(quote_amount_kobo(500, 100, 0, 0, 1000, 0), 60000)
