"""Google OIDC authorization-code login; separate provider identity, no automatic email linking."""
import os
import secrets
from urllib.parse import urlencode
import requests
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from django.contrib.auth import get_user_model, login
from django.db import IntegrityError, transaction
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.views.decorators.http import require_GET
from .models import RiderProfile
from .google_models import GoogleIdentity

AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
RETURN_PATH = '/app/passenger/home.html'
PROFILE_PATH = '/app/passenger/profile.html'
WELCOME_PATH = '/app/passenger/index.html'

def configuration():
    return (os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '').strip(),
            os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '').strip(),
            os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', '').strip())

@require_GET
def google_start(request):
    client_id, secret, redirect_uri = configuration()
    if not all((client_id, secret, redirect_uri)):
        return HttpResponseBadRequest('Google authentication is not configured yet.')
    # Strict approved redirect URI: never derive from untrusted Host or return URL.
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state
    request.session['google_oauth_nonce'] = nonce
    params = {'client_id':client_id,'redirect_uri':redirect_uri,'response_type':'code',
              'scope':'openid email profile','state':state,'nonce':nonce,
              'prompt':'select_account'}
    return HttpResponseRedirect(AUTH_URL + '?' + urlencode(params))

@require_GET
def google_callback(request):
    expected_state = request.session.pop('google_oauth_state', None)
    expected_nonce = request.session.pop('google_oauth_nonce', None)
    supplied = request.GET.get('state', '')
    code = request.GET.get('code', '')
    if not (expected_state and expected_nonce and supplied and secrets.compare_digest(expected_state,supplied) and code):
        return HttpResponseBadRequest('Google login cancelled or session expired. Try again.')
    client_id, client_secret, redirect_uri = configuration()
    if not all((client_id, client_secret, redirect_uri)):
        return HttpResponseBadRequest('Google login is not configured.')
    try:
        response = requests.post(TOKEN_URL, data={'code': code,'client_id':client_id,
            'client_secret':client_secret,'redirect_uri':redirect_uri,'grant_type':'authorization_code'}, timeout=12)
        response.raise_for_status()
        credential = response.json().get('id_token')
        if not credential: raise ValueError('Google did not return an ID token')
        claims = id_token.verify_oauth2_token(credential, Request(), client_id)
        sub = str(claims.get('sub', ''))
        if not sub or claims.get('iss') not in ('accounts.google.com', 'https://accounts.google.com'):
            raise ValueError('Google issuer/subject invalid')
        if not secrets.compare_digest(str(claims.get('nonce', '')), expected_nonce):
            raise ValueError('Google nonce mismatch')
        if claims.get('email_verified') is not True:
            raise ValueError('Google email not verified')
        email = str(claims.get('email', '')).strip().lower()
        if not email or len(email)>254: raise ValueError('Invalid email')
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return HttpResponseBadRequest('Google authentication failed. Please try again.')
    User = get_user_model()
    identity = GoogleIdentity.objects.select_related('user').filter(sub=sub).first()
    if identity:
        user = identity.user
        if not user.is_active: return HttpResponseBadRequest('This account is disabled.')
    else:
        # Never attach to existing email or overwrite phone-verified identity.
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            return HttpResponseBadRequest('This email already belongs to a MoveGo account. Sign in with your original method; account linking is not enabled.')
        try:
            with transaction.atomic():
                user = User(username=email, email=email, first_name=str(claims.get('given_name',''))[:150],
                            last_name=str(claims.get('family_name',''))[:150])
                user.set_unusable_password()
                user.save()
                RiderProfile.objects.create(user=user, role='passenger', phone_verified=False)
                GoogleIdentity.objects.create(user=user, sub=sub)
        except IntegrityError:
            return HttpResponseBadRequest('Account conflict. Please try again.')
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    profile = getattr(user, 'movego_profile', None)
    if profile and profile.role == 'driver':
        return HttpResponseRedirect('/app/driver/home.html')
    # Google verifies email, not phone: collect a verified mobile before ride access.
    if not profile or not profile.phone_verified:
        return HttpResponseRedirect('/app/passenger/phone.html')
    return HttpResponseRedirect(RETURN_PATH if user.first_name.strip() else PROFILE_PATH)
