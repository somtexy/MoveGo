"""MoveGo Step 44: Paystack test checkout / verify / signed webhook; cash reported separately.

Never let the browser supply prices. Test secret keys only. No automated driver payouts.
"""
import hashlib
import hmac
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_GET, require_POST
from apps.accounts.models import RiderProfile
from .models import Ride
from .payment_models import RidePayment

BASE = 'https://api.paystack.co'

def err(message, code=400):
    return JsonResponse({'error': message}, status=code, headers={'Cache-Control': 'no-store'})

def authorized(request):
    if not request.user.is_authenticated: return err('Authentication required.', 401)
    if not RiderProfile.objects.filter(user_id=request.user.pk, phone_verified=True).exists():
        return err('Verified account required.', 403)
    return None

def payload(request):
    if request.content_type != 'application/json' or len(request.body) > 2048:
        raise ValueError('Expected a small JSON object.')
    obj = json.loads(request.body)
    if not isinstance(obj, dict): raise ValueError('Expected JSON object.')
    return obj

def total(ride):
    # Final fare is set only by backend; fallback is its frozen initial backend quote.
    value = ride.final_fare_kobo if ride.final_fare_kobo is not None else ride.estimated_fare_kobo
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        return None
    return value

def secret():
    value = os.environ.get('PAYSTACK_SECRET_KEY','').strip()
    if not value.startswith('sk_test_'):
        return None
    return value

def paystack_call(method, path, body=None):
    key = secret()
    if not key: raise RuntimeError('Paystack TEST secret key is not configured.')
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req=urllib.request.Request(BASE+path, data=data, method=method, headers={
        'Authorization':'Bearer '+key, 'Content-Type':'application/json', 'Accept':'application/json'})
    with urllib.request.urlopen(req, timeout=12) as response:
        result = json.load(response)
    if not isinstance(result,dict) or result.get('status') is not True or not isinstance(result.get('data'),dict):
        raise RuntimeError('Unexpected response from payment provider.')
    return result['data']

def public(payment):
    return {'ride_id':payment.ride_id,'method':payment.method,'status':payment.status,
            'amount_kobo':payment.amount_kobo,'currency':payment.currency,
            'reference':payment.reference if payment.method==RidePayment.Method.PAYSTACK else None,
            'note':'Cash collection reported by driver; not independently verified.' if payment.status==RidePayment.Status.CASH_RECORDED else None}

def verify_data(payment, data):
    # A successful API envelope is NOT a successful payment.
    if data.get('status') != 'success' or data.get('reference') != payment.reference:
        return False
    if type(data.get('amount')) is not int or data['amount'] != payment.amount_kobo:
        return False
    if data.get('currency') != 'NGN' or data.get('domain') != 'test':
        return False
    return True

def finish_payment(reference, data):
    with transaction.atomic():
        payment=RidePayment.objects.select_for_update().filter(reference=reference,method=RidePayment.Method.PAYSTACK).first()
        if payment is None:return None
        if payment.status == RidePayment.Status.PAID:return payment
        if not verify_data(payment,data):return None
        if payment.ride.status != Ride.Status.COMPLETED:return None
        payment.status=RidePayment.Status.PAID
        payment.provider_id=str(data.get('id') or '')[:40]
        payment.save(update_fields=['status','provider_id','updated_at'])
        return payment

@require_POST
@csrf_protect
def initialize(request, ride_id):
    blocked=authorized(request)
    if blocked is not None:return blocked
    try:
        obj=payload(request)
        if obj != {}:return err('No payment amount or fields accepted.')
    except (ValueError,UnicodeError):return err('Expected an empty JSON object.')
    ride=Ride.objects.filter(pk=ride_id,passenger_id=request.user.pk,status=Ride.Status.COMPLETED).first()
    if ride is None:return err('Completed ride not found.',404)
    if not request.user.email:return err('Add a valid account email before checkout.',409)
    try:
        from django.core.validators import validate_email
        validate_email(request.user.email)
    except Exception:return err('Add a valid account email before checkout.',409)
    if not secret():return err('Paystack test mode is not configured.',503)
    amount=total(ride)
    if amount is None:return err('Ride fare unavailable.',409)
    with transaction.atomic():
        ride=Ride.objects.select_for_update().get(pk=ride.pk)
        payment=RidePayment.objects.select_for_update().filter(ride=ride).first()
        if payment is not None:return err('Payment already initiated or recorded for this ride.',409)
        reference='MG'+secrets.token_hex(16)
        payment=RidePayment.objects.create(ride=ride,method='paystack',status='pending',amount_kobo=amount,reference=reference)
    try:
        data=paystack_call('POST','/transaction/initialize',{'email':request.user.email,'amount':amount,
            'currency':'NGN','reference':reference,'metadata':{'ride_id':ride.pk}})
        url=data.get('authorization_url','')
        if (not isinstance(url,str) or not url.startswith('https://checkout.paystack.com/')
                or data.get('reference') != reference):raise RuntimeError('Invalid checkout response.')
    except (RuntimeError,urllib.error.URLError,TimeoutError,ValueError,KeyError):
        # Don't allow a different reference/amount to be paid on retry. If provider accepted
        # the request but network failed, support should reconcile this pending reference.
        return err('Could not initialize checkout. Please contact support if this repeats.',502)
    return JsonResponse({'authorization_url':url,'reference':reference,'amount_kobo':amount,'mode':'test'},headers={'Cache-Control':'no-store'})

@require_POST
@csrf_protect
def verify(request,ride_id):
    blocked=authorized(request)
    if blocked is not None:return blocked
    try:
        obj=payload(request)
        if obj != {}:return err('No verification fields accepted.')
    except (ValueError,UnicodeError):return err('Expected an empty JSON object.')
    payment=RidePayment.objects.select_related('ride').filter(ride_id=ride_id,ride__passenger_id=request.user.pk,method='paystack').first()
    if not payment:return err('Payment not found.',404)
    if payment.status == 'paid':return JsonResponse({'payment':public(payment)},headers={'Cache-Control':'no-store'})
    try:data=paystack_call('GET','/transaction/verify/'+urllib.parse.quote(payment.reference,safe=''))
    except (RuntimeError,urllib.error.URLError,TimeoutError,ValueError):return err('Unable to verify payment right now.',502)
    payment=finish_payment(payment.reference,data)
    if payment is None:return err('Payment is not confirmed. Check status later.',409)
    return JsonResponse({'payment':public(payment)},headers={'Cache-Control':'no-store'})

@require_POST
@csrf_protect
def cash(request,ride_id):
    blocked=authorized(request)
    if blocked is not None:return blocked
    try:
        obj=payload(request)
        if obj != {'confirm_collected':True}:return err('Driver must confirm cash collected.')
    except (ValueError,UnicodeError):return err('Invalid JSON.')
    with transaction.atomic():
        ride=Ride.objects.select_for_update().filter(pk=ride_id,driver_id=request.user.pk,status=Ride.Status.COMPLETED).first()
        if not ride:return err('Completed assigned trip not found.',404)
        if not RiderProfile.objects.filter(user=request.user,role=RiderProfile.Role.DRIVER).exists():
            return err('Driver account required.',403)
        if RidePayment.objects.filter(ride=ride).exists():return err('Payment already recorded.',409)
        amount=total(ride)
        if amount is None:return err('Fare unavailable.',409)
        payment=RidePayment.objects.create(ride=ride,method='cash',status='cash_recorded',amount_kobo=amount,recorded_by=request.user)
    return JsonResponse({'payment':public(payment)},headers={'Cache-Control':'no-store'})

@require_GET
def status(request,ride_id):
    blocked=authorized(request)
    if blocked is not None:return blocked
    ride=Ride.objects.filter(pk=ride_id).first()
    if not ride or request.user.pk not in (ride.passenger_id,ride.driver_id):return err('Ride not found.',404)
    payment=RidePayment.objects.filter(ride=ride).first()
    return JsonResponse({'ride_status':ride.status,'payment':public(payment) if payment else None,
                         'fare_kobo':total(ride)},headers={'Cache-Control':'no-store'})

@csrf_exempt
@require_POST
def webhook(request):
    key=secret()
    if not key:return err('Not configured.',503)
    if len(request.body)>65536:return err('Payload too large.',413)
    signature=request.headers.get('x-paystack-signature','')
    expected=hmac.new(key.encode(),request.body,hashlib.sha512).hexdigest()
    if not hmac.compare_digest(signature,expected):return err('Invalid signature.',403)
    try:event=json.loads(request.body)
    except (ValueError,UnicodeError):return err('Invalid payload.')
    if not isinstance(event,dict):return err('Invalid payload.')
    if event.get('event')=='charge.success':
        candidate=event.get('data')
        reference=candidate.get('reference') if isinstance(candidate,dict) else None
        if isinstance(reference,str) and 0<len(reference)<=80:
            # Re-query Paystack; signed notification is not our final authority on amount/status.
            try:
                verified=paystack_call('GET','/transaction/verify/'+urllib.parse.quote(reference,safe=''))
                finish_payment(reference,verified)
            except (RuntimeError,urllib.error.URLError,TimeoutError,ValueError):
                return err('Temporary verification failure.',503)
    return JsonResponse({'received':True})

@require_GET
def latest(request):
    blocked=authorized(request)
    if blocked is not None:return blocked
    is_driver=RiderProfile.objects.filter(user=request.user,role=RiderProfile.Role.DRIVER).exists()
    rides=Ride.objects.filter(status=Ride.Status.COMPLETED)
    rides=rides.filter(driver_id=request.user.pk) if is_driver else rides.filter(passenger_id=request.user.pk)
    ride=rides.order_by('-updated_at','-id').first()
    if not ride:return JsonResponse({'ride':None},headers={'Cache-Control':'no-store'})
    payment=RidePayment.objects.filter(ride=ride).first()
    return JsonResponse({'ride':{'id':ride.pk,'pickup':ride.pickup_label,'destination':ride.destination_label,
        'status':ride.status,'fare_kobo':total(ride),'payment':public(payment) if payment else None}},
        headers={'Cache-Control':'no-store'})
