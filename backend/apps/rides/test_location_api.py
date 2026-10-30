import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings


@override_settings(ROOT_URLCONF='config.urls')
class LocationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='maps@example.com', email='maps@example.com', password='Pass12345!')

    def test_anonymous_rejected(self):
        self.assertEqual(self.client.get('/api/locations/autocomplete/?q=Abuja').status_code, 401)
        self.assertEqual(self.client.post('/api/locations/route/', data='{}', content_type='application/json').status_code, 401)

    @patch('apps.rides.location_api._fetch')
    def test_nigerian_autocomplete(self, fake):
        self.client.force_login(self.user)
        fake.return_value = ({'results': [
            {'formatted': 'Wuse, Abuja, Nigeria', 'country_code': 'ng', 'lat': 9.08, 'lon': 7.49},
            {'formatted': 'Somewhere else', 'country_code': 'gb', 'lat': 51.5, 'lon': -0.1},
        ]}, None)
        response = self.client.get('/api/locations/autocomplete/?q=Wuse')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)
        self.assertEqual(fake.call_args.args[0], 'geocode/autocomplete')

    @patch('apps.rides.location_api._fetch')
    def test_driving_route(self, fake):
        self.client.force_login(self.user)
        fake.return_value = ({'results': [{'distance': 8100, 'time': 1020}]}, None)
        response = self.client.post('/api/locations/route/', data=json.dumps({'pickup': {'lat':9.08,'lon':7.49}, 'destination': {'lat':9.11,'lon':7.55}}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['distance_km'], 8.1)
        self.assertIsNone(response.json()['fare'])

    def test_invalid_route(self):
        self.client.force_login(self.user)
        response = self.client.post('/api/locations/route/', data=json.dumps({'pickup': {'lat':9.1,'lon':7.5}, 'destination': {'lat':9.1,'lon':7.5}}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
