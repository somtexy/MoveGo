"""Fresh-SMS PIN recovery; never uses phone login's account-switching handler."""
import json
import logging
import re
from datetime import timedelta
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from .models import RiderProfile, PhoneOTP
from .pin_models import AppPIN
from .twilio_verify import twilio_service
from .otp import normalize_phone

log = logging.getLogger(__name__)
RECOVERY_KEY = 'movego_pin_recovery_confirmed'
START_KEY = 'movego_pin_recovery_started'
VERIFIED_LIFETIME = 300
def error(msg, status=400): return JsonResponse({'error':msg},status=status)
def data_for(request):
    try:
        obj=json.loads(request.body)
        return obj if isinstance(obj,dict) else {}
    except (ValueError,UnicodeError): return {}
def profile_for(request):
    if not request.user.is_authenticated: return None, error('Please sign in.',401)
    profile=RiderProfile.objects.filter(user=request.user,phone_verified=True).first()
    if not profile or not normalize_phone(profile.phone): return None,error('Verify your phone number first.',403)
    if not AppPIN.objects.filter(user=request.user).exists(): return None,error('Create a PIN first.',404)
    return profile,None

@csrf_protect
@require_POST
def request_code(request):
    profile,denied=profile_for(request)
    if denied is not None:return denied
    request.session.pop(RECOVERY_KEY,None)
    phone=normalize_phone(profile.phone)
    now=timezone.now()
    with transaction.atomic():
        PhoneOTP.objects.get_or_create(phone=phone)
        row=PhoneOTP.objects.select_for_update().get(phone=phone)
        if row.last_sent_at and now-row.last_sent_at < timedelta(seconds=60):
            return error('Please wait 60 seconds before requesting another code.',429)
        if not row.window_started_at or now-row.window_started_at >= timedelta(hours=1):
            row.window_started_at=now
            row.sends_in_window=0
        if row.sends_in_window>=5:return error('Too many SMS requests. Try again later.',429)
        try:
            result=twilio_service().verifications.create(to=phone,channel='sms')
            if result.status!='pending':return error('Could not send recovery SMS.',503)
        except Exception:
            log.exception('PIN recovery SMS request failed')
            return error('SMS recovery is currently unavailable.',503)
        row.last_sent_at=now
        row.expires_at=now+timedelta(minutes=10)
        row.sends_in_window+=1
        row.attempts=0
        row.verified_at=None
        row.code_digest=''
        row.save()
    request.session[START_KEY]={'uid':request.user.pk,'phone':phone,'at':int(now.timestamp())}
    return JsonResponse({'ok':True,'message':'Code sent to your verified phone number.','resend_after_seconds':60})

@csrf_protect
@require_POST
def confirm_code(request):
    profile,denied=profile_for(request)
    if denied is not None:return denied
    payload=data_for(request)
    code=payload.get('code')
    if not isinstance(code,str) or not re.fullmatch(r'[0-9]{6,8}',code):return error('Enter the SMS verification code.')
    started=request.session.get(START_KEY)
    phone=normalize_phone(profile.phone)
    now=timezone.now()
    if not isinstance(started,dict) or started.get('uid')!=request.user.pk or started.get('phone')!=phone or now.timestamp()-started.get('at',0)>600:
        return error('Request a new recovery SMS.',403)
    with transaction.atomic():
        row=PhoneOTP.objects.select_for_update().filter(phone=phone).first()
        if not row or row.verified_at or not row.last_sent_at or (row.expires_at and now>row.expires_at):
            return error('Request a new recovery SMS.')
        if row.attempts>=5:return error('Too many attempts. Request another code.',429)
        row.attempts+=1
        row.save(update_fields=['attempts'])
    try:
        result=twilio_service().verification_checks.create(to=phone,code=code)
    except Exception:
        log.exception('PIN recovery SMS validation failed')
        return error('Unable to verify code right now.',503)
    if result.status!='approved':return error('Incorrect or expired SMS code.')
    with transaction.atomic():
        row=PhoneOTP.objects.select_for_update().get(phone=phone)
        if row.verified_at:return error('Code already used.',409)
        row.verified_at=now
        row.save(update_fields=['verified_at'])
    request.session.pop(START_KEY,None)
    request.session[RECOVERY_KEY]={'uid':request.user.pk,'at':int(now.timestamp())}
    return JsonResponse({'ok':True,'message':'Phone verified. Choose a new PIN.'})

@csrf_protect
@require_POST
def reset_pin(request):
    profile,denied=profile_for(request)
    if denied is not None:return denied
    proof=request.session.get(RECOVERY_KEY)
    now=timezone.now()
    if not isinstance(proof,dict) or proof.get('uid')!=request.user.pk or now.timestamp()-proof.get('at',0)>VERIFIED_LIFETIME:
        return error('Verify a fresh SMS code to reset your PIN.',403)
    payload=data_for(request)
    pin=payload.get('pin'); confirm=payload.get('confirm')
    if not isinstance(pin,str) or not re.fullmatch(r'[0-9]{6}',pin) or pin!=confirm:
        return error('Enter and confirm the same six-digit PIN.')
    with transaction.atomic():
        record=AppPIN.objects.select_for_update().filter(user=request.user).first()
        if record is None:return error('Create a PIN first.',404)
        record.encoded_pin=make_password(pin)
        record.failed_attempts=0
        record.locked_until=None
        record.save(update_fields=['encoded_pin','failed_attempts','locked_until','updated_at'])
    request.session.pop(RECOVERY_KEY,None)
    request.session.pop('movego_pin_recently_verified',None)
    return JsonResponse({'ok':True,'message':'PIN reset. Verify your new PIN.'})
