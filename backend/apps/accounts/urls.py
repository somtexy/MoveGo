from django.urls import path, include
from . import views, otp, twilio_verify, profile_api

urlpatterns = [
    path("pin/", include("apps.accounts.pin_urls")),
    path("profile/", profile_api.profile_detail, name="auth-profile"),
    path("phone/twilio/request/", twilio_verify.request_sms, name="twilio-otp-request"),
    path("phone/twilio/check/", twilio_verify.check_sms, name="twilio-otp-check"),
    path("phone/request-otp/", otp.request_code, name="phone-otp-request"),
    path("phone/verify-otp/", otp.verify_code, name="phone-otp-verify"),
    path("csrf/", views.csrf, name="auth-csrf"),
    path("register/", views.register, name="auth-register"),
    path("login/", views.sign_in, name="auth-login"),
    path("logout/", views.sign_out, name="auth-logout"),
    path("me/", views.me, name="auth-me"),
]

from . import google_auth
urlpatterns += [
    path("google/start/", google_auth.google_start, name="google-start"),
    path("google/callback/", google_auth.google_callback, name="google-callback"),
]
