"""MoveGo Twilio Verify SMS endpoints. No SMS is sent without credentials."""
import logging
import os
import re
from datetime import timedelta

from django.contrib.auth import get_user_model, login
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .models import PhoneOTP, RiderProfile
from .otp import normalize_phone, parse

logger = logging.getLogger(__name__)
COOLDOWN = timedelta(seconds=60)
WINDOW = timedelta(hours=1)
MAX_SENDS = 5
MAX_CHECKS = 5


def fail(message, status=400):
    return JsonResponse({"error": message}, status=status)


def twilio_service():
    # Load secrets from environment, never browser code or public repositories.
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    service_sid = os.environ.get("TWILIO_VERIFY_SERVICE_SID", "")
    if not (sid.startswith("AC") and token and service_sid.startswith("VA")):
        raise RuntimeError("Twilio Verify is not configured")
    from twilio.rest import Client
    return Client(sid, token).verify.v2.services(service_sid)


@require_POST
@csrf_protect
def request_sms(request):
    data = parse(request)
    phone = normalize_phone(data.get("phone")) if data else None
    if not phone:
        return fail("Enter a valid Nigerian mobile number.")
    # Do not send OTP to a known conflicting number in a Google linking session.
    from .google_models import GoogleIdentity
    if request.user.is_authenticated and GoogleIdentity.objects.filter(user_id=request.user.pk).exists():
        owner = RiderProfile.objects.filter(phone=phone, phone_verified=True).exclude(user_id=request.user.pk).exists()
        if owner:
            return fail('This phone number already belongs to another MoveGo account.', 409)
    try:
        service = twilio_service()
    except (RuntimeError, ImportError):
        return fail("SMS verification is not configured.", 503)

    now = timezone.now()
    # Serializes per-phone requests under PostgreSQL. For high-volume production,
    # add IP/device rate limits and durable distributed throttling as well.
    with transaction.atomic():
        PhoneOTP.objects.get_or_create(phone=phone)
        record = PhoneOTP.objects.select_for_update().get(phone=phone)
        if record.last_sent_at and now - record.last_sent_at < COOLDOWN:
            return fail("Please wait before requesting another code.", 429)
        if not record.window_started_at or now - record.window_started_at >= WINDOW:
            record.window_started_at = now
            record.sends_in_window = 0
        if record.sends_in_window >= MAX_SENDS:
            return fail("Too many requests. Try again later.", 429)
        try:
            response = service.verifications.create(to=phone, channel="sms")
            if response.status != "pending":
                return fail("Unable to send verification code.", 503)
        except Exception:
            logger.exception("Twilio SMS start failed")
            return fail("Unable to send verification code.", 503)
        record.window_started_at = record.window_started_at or now
        record.last_sent_at = now
        record.expires_at = now + timedelta(minutes=10)  # Display only; Twilio controls actual expiry.
        record.sends_in_window += 1
        record.attempts = 0
        record.verified_at = None
        record.code_digest = ""  # Never mix the previous local OTP with Twilio Verify.
        record.save()
    return JsonResponse({"message": "If eligible, a verification SMS has been requested.", "resend_after_seconds": 60})


@require_POST
@csrf_protect
def check_sms(request):
    data = parse(request)
    phone = normalize_phone(data.get("phone")) if data else None
    code = data.get("code") if data else None
    if not phone or not isinstance(code, str) or not re.fullmatch(r"\d{6,8}", code):
        return fail("Enter a valid phone number and verification code.")
    try:
        service = twilio_service()
    except (RuntimeError, ImportError):
        return fail("SMS verification is not configured.", 503)

    now = timezone.now()
    # Record a check before calling the remote service, including failed checks.
    with transaction.atomic():
        record = PhoneOTP.objects.select_for_update().filter(phone=phone).first()
        if not record or not record.last_sent_at or record.verified_at:
            return fail("Request a new verification code.")
        if record.attempts >= MAX_CHECKS:
            return fail("Too many attempts. Request another code.", 429)
        record.attempts += 1
        record.save(update_fields=["attempts"])
    try:
        result = service.verification_checks.create(to=phone, code=code)
    except Exception:
        logger.exception("Twilio SMS check failed")
        return fail("Could not verify the code. Try again.", 503)
    if result.status != "approved":
        return fail("Incorrect or expired verification code.")

    with transaction.atomic():
        record = PhoneOTP.objects.select_for_update().get(phone=phone)
        if record.verified_at:
            return fail("Code already used. Request another.")
        # A Google session can link a newly verified phone, never switch accounts.
        from .google_models import GoogleIdentity
        is_google_session = (request.user.is_authenticated and
                             GoogleIdentity.objects.filter(user_id=request.user.pk).exists())
        if is_google_session:
            existing = RiderProfile.objects.select_for_update().filter(phone=phone, phone_verified=True).exclude(user_id=request.user.pk).first()
            if existing:
                return fail('This phone number is already linked to another MoveGo account. Sign in to that account or contact support.', 409)
            user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
            profile = RiderProfile.objects.select_for_update().filter(user=user).first()
            if not profile:
                return fail('Your account profile is missing. Contact support.', 409)
            if profile.phone_verified and profile.phone != phone:
                return fail('Your account already has a verified phone number. Contact support to change it.', 409)
            profile.phone = phone
            profile.phone_verified = True
            profile.save(update_fields=['phone', 'phone_verified'])
        else:
            profile = RiderProfile.objects.select_related("user").filter(phone=phone, phone_verified=True).first()
            if profile:
                user = profile.user
            else:
                User = get_user_model()
                username = "phone_" + phone[1:]
                user = User.objects.filter(username=username).first()
                if user:
                    profile = RiderProfile.objects.filter(user=user).first()
                    if not profile or profile.phone not in ("", phone):
                        return fail("Account conflict. Contact support.", 409)
                    profile.phone = phone
                    profile.phone_verified = True
                    profile.save(update_fields=["phone", "phone_verified"])
                else:
                    user = User(username=username)
                    user.set_unusable_password()
                    try:
                        user.save()
                        RiderProfile.objects.create(user=user, role="passenger", phone=phone, phone_verified=True)
                    except IntegrityError:
                        return fail("Account conflict. Try again.", 409)
        record.verified_at = timezone.now()
        record.code_digest = ""
        record.save(update_fields=["verified_at", "code_digest"])
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse({"message": "Phone verified.", "phone_verified": True, "user_id": user.pk, "next_url": "/app/passenger/role.html"})
