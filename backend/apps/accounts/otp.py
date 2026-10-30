"""Phone OTP logic. Only +234 numbers are supported in this first stage."""
import hashlib
import hmac
import json
import re
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .models import PhoneOTP, RiderProfile

EXPIRY = timedelta(minutes=5)
COOLDOWN = timedelta(seconds=60)
WINDOW = timedelta(hours=1)
MAX_SENDS = 5
MAX_ATTEMPTS = 5

def normalize_phone(value):
    if not isinstance(value, str):
        return None
    cleaned = re.sub(r"[ ()-]", "", value)
    if cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = "+234" + cleaned[1:]
    elif cleaned.startswith("234") and len(cleaned) == 13:
        cleaned = "+" + cleaned
    return cleaned if re.fullmatch(r"\+234[789]\d{9}", cleaned or "") else None

def digest(phone, code):
    message = f"movego-phone-otp:{phone}:{code}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()

def parse(request):
    if request.content_type != "application/json" or len(request.body) > 2048:
        return None
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None

def reject(message, status=400):
    return JsonResponse({"error": message}, status=status)

def send_code(phone, code):
    """Replace this with a real provider adapter in the delivery integration step."""
    if settings.DEBUG and getattr(settings, "MOVEGO_OTP_DEV_CONSOLE", False):
        print(f"[MOVEGO LOCAL DEV OTP ONLY] {phone}: {code}", flush=True)
        return
    raise RuntimeError("Phone OTP delivery provider is not configured")

@require_POST
@csrf_protect
def request_code(request):
    data = parse(request)
    phone = normalize_phone(data.get("phone")) if data else None
    if not phone:
        return reject("Enter a valid Nigerian mobile number.")
    # Refuse to create an unusable OTP when delivery isn't configured.
    if not (settings.DEBUG and getattr(settings, "MOVEGO_OTP_DEV_CONSOLE", False)):
        return reject("Phone verification delivery is not configured yet.", 503)
    now = timezone.now()
    with transaction.atomic():
        record, _ = PhoneOTP.objects.get_or_create(phone=phone)
        record = PhoneOTP.objects.select_for_update().get(pk=record.pk)
        if record.last_sent_at and now - record.last_sent_at < COOLDOWN:
            return reject("Please wait before requesting another code.", 429)
        if not record.window_started_at or now - record.window_started_at >= WINDOW:
            record.window_started_at = now
            record.sends_in_window = 0
        if record.sends_in_window >= MAX_SENDS:
            return reject("Too many codes requested. Try again later.", 429)
        code = f"{secrets.randbelow(10000):04d}"
        try:
            send_code(phone, code)
        except Exception:
            return reject("Unable to send verification code.", 503)
        record.code_digest = digest(phone, code)
        record.expires_at = now + EXPIRY
        record.last_sent_at = now
        record.sends_in_window += 1
        record.attempts = 0
        record.verified_at = None
        record.save()
    return JsonResponse({"message": "Verification code issued.", "expires_in_seconds": 300, "resend_after_seconds": 60})

@require_POST
@csrf_protect
def verify_code(request):
    data = parse(request)
    phone = normalize_phone(data.get("phone")) if data else None
    code = data.get("code") if data else None
    if not phone or not isinstance(code, str) or not re.fullmatch(r"\d{4}", code):
        return reject("Enter a valid phone number and four-digit code.")
    now = timezone.now()
    with transaction.atomic():
        record = PhoneOTP.objects.select_for_update().filter(phone=phone).first()
        if not record or not record.code_digest or not record.expires_at or now >= record.expires_at or record.attempts >= MAX_ATTEMPTS:
            return reject("Code expired or invalid. Request a new code.", 400)
        if not hmac.compare_digest(record.code_digest, digest(phone, code)):
            record.attempts += 1
            if record.attempts >= MAX_ATTEMPTS:
                record.code_digest = ""
            record.save(update_fields=["attempts", "code_digest"])
            return reject("Code expired or invalid. Request a new code.", 400)
        # Existing accounts must not have the same phone attached to more than one profile.
        profile = RiderProfile.objects.select_for_update().filter(phone=phone, phone_verified=True).first()
        if profile:
            user = profile.user
        else:
            User = get_user_model()
            username = "phone_" + phone[1:]
            user = User.objects.filter(username=username).first()
            if user is not None and user.movego_profile.phone != phone:
                return reject("Account conflict. Contact support.", 409)
            if user is None:
                user = User(username=username, first_name="")
                user.set_unusable_password()
                user.save()
                RiderProfile.objects.create(user=user, role="passenger", phone=phone, phone_verified=True)
            else:
                profile = user.movego_profile
                profile.phone = phone
                profile.phone_verified = True
                profile.save(update_fields=["phone", "phone_verified"])
        record.code_digest = ""
        record.verified_at = now
        record.save(update_fields=["code_digest", "verified_at"])
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse({"message": "Phone verified", "user_id": user.pk, "phone_verified": True})
