from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from .google_models import GoogleIdentity
from .models import RiderProfile

@patch('apps.accounts.google_auth.configuration', return_value=('test-client','test-secret','http://testserver/api/auth/google/callback/'))
class GoogleAuthTests(TestCase):
    def test_google_start_and_reject_missing_state(self, _config):
        response = self.client.get('/api/auth/google/start/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('accounts.google.com', response['Location'])
        self.assertEqual(self.client.get('/api/auth/google/callback/?code=abc').status_code, 400)

    @patch('apps.accounts.google_auth.id_token.verify_oauth2_token')
    @patch('apps.accounts.google_auth.requests.post')
    def test_new_and_returning_google_account(self, post, verify, _config):
        post.return_value = Mock(status_code=200, json=lambda: {'id_token': 'token'})
        for i in range(2):
            self.client.get('/api/auth/google/start/')
            session = self.client.session
            verify.return_value = {
                'sub': 'fixed-google-id', 'iss': 'https://accounts.google.com',
                'email_verified': True, 'email': 'newuser@example.com',
                'given_name': 'Ada', 'nonce': session['google_oauth_nonce'],
            }
            response = self.client.get('/api/auth/google/callback/', {
                'state': session['google_oauth_state'], 'code': 'code'
            })
            self.assertEqual(response.status_code, 302)
        self.assertEqual(GoogleIdentity.objects.count(), 1)
        self.assertEqual(get_user_model().objects.filter(email='newuser@example.com').count(), 1)
        self.assertFalse(RiderProfile.objects.get(user__email='newuser@example.com').phone_verified)

    @patch('apps.accounts.google_auth.id_token.verify_oauth2_token')
    @patch('apps.accounts.google_auth.requests.post')
    def test_no_silent_email_link(self, post, verify, _config):
        User = get_user_model()
        User.objects.create_user(username='taken@example.com', email='taken@example.com', password='verystrong-test-password')
        self.client.get('/api/auth/google/start/')
        session = self.client.session
        post.return_value = Mock(status_code=200, json=lambda: {'id_token': 'token'})
        verify.return_value = {
            'sub': 'google-account-other', 'iss': 'https://accounts.google.com',
            'email_verified': True, 'email': 'taken@example.com',
            'nonce': session['google_oauth_nonce'],
        }
        response = self.client.get('/api/auth/google/callback/', {
            'state': session['google_oauth_state'], 'code': 'code'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GoogleIdentity.objects.count(), 0)

    @patch('apps.accounts.google_auth.id_token.verify_oauth2_token')
    @patch('apps.accounts.google_auth.requests.post')
    def test_wrong_nonce_is_rejected(self, post, verify, _config):
        self.client.get('/api/auth/google/start/')
        session = self.client.session
        post.return_value = Mock(status_code=200, json=lambda: {'id_token': 'token'})
        verify.return_value = {
            'sub': 'newsub', 'iss': 'https://accounts.google.com',
            'email_verified': True, 'email': 'any@example.com', 'nonce': 'wrong',
        }
        response = self.client.get('/api/auth/google/callback/', {'state':session['google_oauth_state'], 'code':'code'})
        self.assertEqual(response.status_code, 400)
