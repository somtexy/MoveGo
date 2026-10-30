"""Step 34 revised identity document submission tests."""
import io
import tempfile
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from apps.accounts.models import RiderProfile
from .models import DriverProfile

DATA = {'first_name': 'Ada', 'last_name': 'Driver', 'nin': '12345678901',
        'license_number': 'FCT-124557', 'vehicle_make': 'Toyota',
        'vehicle_model': 'Corolla', 'vehicle_color': 'White', 'plate_number': 'ABC-123XY'}


def photo(name):
    output = io.BytesIO()
    Image.new('RGB', (300, 300), (40, 120, 80)).save(output, 'JPEG')
    return SimpleUploadedFile(name, output.getvalue(), content_type='image/jpeg')


def application(**updates):
    payload = dict(DATA)
    payload.update({'nin_document': photo('nin.jpg'),
                    'license_photo': photo('licence.jpg'), 'selfie_photo': photo('selfie.jpg')})
    payload.update(updates)
    return payload


class DriverAPITests(TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        for name in ('nin_document', 'license_photo', 'selfie_photo'):
            storage = DriverProfile._meta.get_field(name).storage
            patcher = patch.object(storage, 'location', str(Path(self.folder.name)))
            patcher.start()
            self.addCleanup(patcher.stop)
        self.user = get_user_model().objects.create_user(username='step34', password='secure-password-123')
        self.rp = RiderProfile.objects.create(user=self.user, phone='+2348000000900', phone_verified=True, role='passenger')
        self.client = Client(enforce_csrf_checks=True)
        self.client.get('/api/auth/csrf/')
        self.csrf = self.client.cookies['csrftoken'].value

    def register(self, payload=None, csrf=True):
        return self.client.post('/api/drivers/register/', data=application() if payload is None else payload,
                                **({'HTTP_X_CSRFTOKEN': self.csrf} if csrf else {}))

    def availability(self, value, csrf=True):
        return self.client.post('/api/drivers/availability/',
                                data='{"is_online":' + ('true' if value is True else 'false' if value is False else '"yes"') + '}',
                                content_type='application/json',
                                **({'HTTP_X_CSRFTOKEN': self.csrf} if csrf else {}))

    def test_anonymous_rejected(self):
        self.assertEqual(self.client.get('/api/drivers/me/').status_code, 401)
        self.assertEqual(self.register().status_code, 401)

    def test_csrf_required(self):
        self.client.force_login(self.user)
        self.assertEqual(self.register(csrf=False).status_code, 403)

    def test_verified_phone_required(self):
        self.client.force_login(self.user)
        self.rp.phone_verified = False
        self.rp.save()
        self.assertEqual(self.register().status_code, 403)
        self.assertFalse(DriverProfile.objects.exists())

    def test_registration_pending_and_duplicate(self):
        self.client.force_login(self.user)
        response = self.register()
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()['review_status'], 'pending')
        driver = DriverProfile.objects.get(user=self.user)
        self.assertEqual(driver.first_name, 'Ada')
        self.assertTrue(driver.nin_document.name)
        self.assertTrue(driver.license_photo.name)
        self.assertTrue(driver.selfie_photo.name)
        self.assertEqual(self.register().status_code, 409)
        self.assertNotIn('nin', self.client.get('/api/drivers/me/').json())
        self.assertNotIn('license_number', self.client.get('/api/drivers/me/').json())

    def test_validation(self):
        self.client.force_login(self.user)
        self.assertEqual(self.register(application(plate_number='<script>')).status_code, 400)
        self.assertEqual(self.register(application(nin='not a NIN')).status_code, 400)
        self.assertEqual(self.register(application(selfie_photo=SimpleUploadedFile('bad.jpg',b'not an image', content_type='image/jpeg'))).status_code, 400)
        self.assertFalse(DriverProfile.objects.exists())

    def test_pending_cannot_go_online_and_approval_allows(self):
        self.client.force_login(self.user)
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.availability(True).status_code, 403)
        driver = DriverProfile.objects.get(user=self.user)
        driver.review_status = 'approved'
        driver.save()
        self.assertEqual(self.availability(True).status_code, 200)
        driver.refresh_from_db()
        self.assertTrue(driver.is_online)
        self.assertEqual(self.availability(False).status_code, 200)

    def test_availability_requires_csrf_and_boolean(self):
        self.client.force_login(self.user)
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.availability(False, csrf=False).status_code, 403)
        self.assertEqual(self.availability('yes').status_code, 400)

    def test_documents_are_admin_only(self):
        self.client.force_login(self.user)
        self.assertEqual(self.register().status_code, 201)
        pk = DriverProfile.objects.get(user=self.user).pk
        url = f'/api/drivers/review-document/{pk}/nin_document/'
        self.assertNotEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get('/api/drivers/me/').json().get('nin'), None)

    def test_photo_exif_removed_on_save(self):
        self.client.force_login(self.user)
        self.assertEqual(self.register().status_code, 201)
        doc = DriverProfile.objects.get(user=self.user).nin_document
        with doc.open('rb') as f:
            with Image.open(f) as img:
                self.assertEqual(img.format, 'JPEG')
                self.assertFalse(img.getexif())
