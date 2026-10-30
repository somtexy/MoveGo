"""Optional app PIN, never a substitute for Django account authentication."""
import json
import re
from datetime import timedelta
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from .models import RiderProfile
from .pin_models import AppPIN
from .pin_guard import mark_verified, clear_verified

PIN_PATTERN = re.compile(r'^[0-9]{6}$')

def reply(message, status=400):
    return JsonResponse({'error': message}, status=status)

def read_json(request):
    try:
        data = json.loads(request.body)
        return data if isinstance(data, dict) else None
    except (UnicodeError, ValueError):
        return None

def eligible(request):
    if not request.user.is_authenticated:
        return reply('Please sign in.', 401)
    profile = RiderProfile.objects.filter(user=request.user).first()
    if not profile or not profile.phone_verified:
        return reply('Verify your phone number first.', 403)
    return None

def valid_pin(pin):
    return isinstance(pin, str) and bool(PIN_PATTERN.fullmatch(pin))

@require_GET
def status(request):
    if not request.user.is_authenticated: return reply('Please sign in.', 401)
    return JsonResponse({'has_pin': AppPIN.objects.filter(user=request.user).exists(),
                         'phone_verified': RiderProfile.objects.filter(user=request.user, phone_verified=True).exists()})

@require_POST
def setup(request):
    denied = eligible(request)
    if denied is not None: return denied
    data=read_json(request)
    if data is None: return reply('Invalid JSON.')
    pin, confirm = data.get('pin'), data.get('confirm')
    if not valid_pin(pin) or pin!=confirm: return reply('Enter and confirm the same six-digit PIN.')
    if AppPIN.objects.filter(user=request.user).exists(): return reply('PIN already exists. Use change or recovery.', 409)
    with transaction.atomic():
        if AppPIN.objects.select_for_update().filter(user=request.user).exists(): return reply('PIN already exists.',409)
        AppPIN.objects.create(user=request.user,encoded_pin=make_password(pin))
    return JsonResponse({'ok':True},status=201)

def attempt(record,pin):
    now=timezone.now()
    if record.locked_until and record.locked_until>now:
        return reply('Too many attempts. Try again later.',429)
    if valid_pin(pin) and check_password(pin,record.encoded_pin):
        record.failed_attempts=0
        record.locked_until=None
        record.save(update_fields=['failed_attempts','locked_until'])
        return None
    record.failed_attempts+=1
    if record.failed_attempts>=5:
        record.failed_attempts=0
        record.locked_until=now+timedelta(minutes=15)
    record.save(update_fields=['failed_attempts','locked_until'])
    return reply('Incorrect PIN.',429 if record.locked_until and record.locked_until>now else 400)

@require_POST
def verify(request):
    denied=eligible(request)
    if denied is not None: return denied
    data=read_json(request)
    if data is None: return reply('Invalid JSON.')
    with transaction.atomic():
        record=AppPIN.objects.select_for_update().filter(user=request.user).first()
        if record is None: return reply('Create your PIN first.',404)
        error=attempt(record,data.get('pin'))
        if error is not None: return error
    mark_verified(request)
    # This verifies only the PIN on an already authenticated session; it does not issue login credentials.
    return JsonResponse({'ok':True})

@require_POST
def change(request):
    denied=eligible(request)
    if denied is not None: return denied
    data=read_json(request)
    if data is None: return reply('Invalid JSON.')
    pin,confirm=data.get('new_pin'),data.get('confirm')
    if not valid_pin(pin) or pin!=confirm:return reply('Enter and confirm the same six-digit new PIN.')
    with transaction.atomic():
        record=AppPIN.objects.select_for_update().filter(user=request.user).first()
        if record is None: return reply('Create your PIN first.',404)
        error=attempt(record,data.get('old_pin'))
        if error is not None: return error
        record.encoded_pin=make_password(pin)
        record.save(update_fields=['encoded_pin','updated_at'])
    clear_verified(request)
    return JsonResponse({'ok':True})

@require_POST
def recover(request):
    # Recovery is intentionally not offered by the existing session alone.
    # A future flow must require fresh reauthentication and OTP confirmation.
    return reply('PIN recovery requires fresh phone verification. Contact support until recovery is enabled.',501)
