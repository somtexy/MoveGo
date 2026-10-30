from django.conf import settings
from django.db import models


class RiderProfile(models.Model):
    class Role(models.TextChoices):
        PASSENGER = "passenger", "Passenger"
        DRIVER = "driver", "Driver"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="movego_profile")
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.PASSENGER)
    phone = models.CharField(max_length=20, blank=True)
    phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class PhoneOTP(models.Model):
    """A single bounded verification challenge per phone number."""
    phone = models.CharField(max_length=16, unique=True)
    code_digest = models.CharField(max_length=64, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    window_started_at = models.DateTimeField(null=True, blank=True)
    sends_in_window = models.PositiveSmallIntegerField(default=0)
    attempts = models.PositiveSmallIntegerField(default=0)
    verified_at = models.DateTimeField(null=True, blank=True)
from .google_models import GoogleIdentity

from .pin_models import AppPIN  # Register with Django

from .avatar_models import AccountAvatar  # noqa: F401  Django model discovery
