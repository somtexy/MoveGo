import io
import tempfile
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from . import avatar_api

class AvatarTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.patch = patch.object(avatar_api, '_directory', return_value=self.folder)
        self.patch.start(); self.addCleanup(self.patch.stop)
        User = get_user_model()
        self.one = User.objects.create_user(username='avatar_one', password='safePass123!')
        self.two = User.objects.create_user(username='avatar_two', password='safePass123!')
        self.url = '/api/auth/avatar/'

    def photo(self):
        b=io.BytesIO(); Image.new('RGB',(25,25),'blue').save(b,format='PNG')
        return SimpleUploadedFile('portrait.png',b.getvalue(),content_type='image/png')

    def test_requires_authentication(self):
        self.assertEqual(self.client.get(self.url).status_code,401)
        self.assertEqual(self.client.post(self.url, {'photo':self.photo()}).status_code,401)
        self.assertEqual(self.client.delete(self.url).status_code,401)

    def test_upload_replace_and_remove(self):
        self.client.force_login(self.one)
        self.assertEqual(self.client.post(self.url, {'photo':self.photo()}).status_code,200)
        response=self.client.get(self.url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response['Content-Type'],'image/webp')
        response.close()  # Release FileResponse handle before replacing on Windows
        self.assertEqual(self.client.post(self.url, {'photo':self.photo()}).status_code,200)
        self.assertEqual(len(list(self.folder.iterdir())),1)
        self.assertEqual(self.client.delete(self.url).status_code,200)
        self.assertEqual(self.client.get(self.url).status_code,404)
        self.assertEqual(len(list(self.folder.iterdir())),0)

    def test_private_per_user(self):
        self.client.force_login(self.one)
        self.client.post(self.url, {'photo':self.photo()})
        self.client.force_login(self.two)
        self.assertEqual(self.client.get(self.url).status_code,404)

    def test_invalid_upload(self):
        self.client.force_login(self.one)
        bad=SimpleUploadedFile('fake.png', b'not image', content_type='image/png')
        self.assertEqual(self.client.post(self.url,{'photo':bad}).status_code,400)
        self.assertEqual(self.client.post(self.url,{'photo':SimpleUploadedFile('big.png',b'a'*(5*1024*1024+1))}).status_code,400)

    def test_csrf_required(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.one)
        self.assertEqual(client.post(self.url, {'photo':self.photo()}).status_code,403)
        self.assertEqual(client.delete(self.url).status_code,403)
