"""Step 42: explicit passenger-initiated offers, private driver polling, atomic acceptance.

No background jobs: passenger must request the next offer after expiry/decline.
"""
import json
import math
from datetime import timedelta
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from apps.accounts.models import RiderProfile
from apps.drivers.models import DriverLocation, DriverProfile
from .discovery_api import distance_km, LOCATION_TTL_SECONDS, MAX_ACCURACY_M, MAX_RADIUS_KM
from .models import Ride
from .offer_models import RideOffer

OFFER_SECONDS = 30
WAITING = (Ride.Status.REQUESTED, Ride.Status.SEARCHING)


def error(message, status):
    return JsonResponse({'error': message}, status=status, headers={'Cache-Control': 'no-store'})


def passenger(request):
    if not request.user.is_authenticated: return error('Login required.', 401)
    if not RiderProfile.objects.filter(user=request.user, role=RiderProfile.Role.PASSENGER, phone_verified=True).exists():
        return error('Verified passenger required.', 403)
    return None


def driver(request):
    if not request.user.is_authenticated: return None, error('Login required.', 401)
    profile = DriverProfile.objects.filter(user=request.user).first()
    if not profile or not RiderProfile.objects.filter(user=request.user, role=RiderProfile.Role.DRIVER, phone_verified=True).exists():
        return None, error('Verified driver required.', 403)
    return profile, None


def expire(ride, now):
    RideOffer.objects.filter(ride=ride, status=RideOffer.Status.PENDING, expires_at__lte=now).update(
        status=RideOffer.Status.EXPIRED, responded_at=now)


def offer_json(offer):
    return {'offer_id': offer.pk, 'ride_id': offer.ride_id,
            'pickup': offer.ride.pickup_label, 'destination': offer.ride.destination_label,
            'category': offer.ride.category, 'estimated_fare_kobo': offer.ride.estimated_fare_kobo,
            'expires_at': offer.expires_at.isoformat()}


@require_POST
@csrf_protect
def request_offer(request, ride_id):
    denied = passenger(request)
    if denied is not None: return denied
    if request.content_type != 'application/json' or len(request.body) > 256: return error('Expected JSON.', 400)
    try:
        if json.loads(request.body) != {}: return error('Send an empty JSON object.', 400)
    except (ValueError, UnicodeError): return error('Invalid JSON.', 400)
    with transaction.atomic():
        ride = Ride.objects.select_for_update().filter(pk=ride_id, passenger_id=request.user.pk).first()
        if ride is None: return error('Ride not found.', 404)
        if ride.status not in WAITING or ride.driver_id is not None: return error('This ride cannot receive offers.', 409)
        if ride.pickup_latitude is None or ride.pickup_longitude is None: return error('Missing pickup coordinates.', 422)
        now = timezone.now()
        expire(ride, now)
        pending = RideOffer.objects.filter(ride=ride, status=RideOffer.Status.PENDING).first()
        if pending: return JsonResponse({'state': 'offered', 'expires_at': pending.expires_at.isoformat(), 'message': 'Awaiting driver response.'}, headers={'Cache-Control':'no-store'})
        excluded = RideOffer.objects.filter(ride=ride).values_list('driver_id', flat=True)
        candidates = DriverLocation.objects.filter(
            driver__review_status=DriverProfile.Review.APPROVED, driver__is_online=True,
            driver__user__movego_profile__role=RiderProfile.Role.DRIVER,
            driver__user__movego_profile__phone_verified=True,
            updated_at__gt=now-timedelta(seconds=LOCATION_TTL_SECONDS),
            accuracy_m__gte=0, accuracy_m__lte=MAX_ACCURACY_M,
        ).exclude(driver__user_id__in=excluded).exclude(driver__user_id=ride.passenger_id).select_related('driver')
        ranked=[]
        for loc in candidates:
            if not all(math.isfinite(float(n)) for n in (loc.latitude, loc.longitude, loc.accuracy_m)):
                continue
            if not (-90<=loc.latitude<=90 and -180<=loc.longitude<=180): continue
            if Ride.objects.filter(driver_id=loc.driver.user_id, status__in=[Ride.Status.ASSIGNED, Ride.Status.ARRIVING, Ride.Status.ARRIVED, Ride.Status.STARTED]).exists(): continue
            if RideOffer.objects.filter(driver_id=loc.driver.user_id, status=RideOffer.Status.PENDING, expires_at__gt=now).exists(): continue
            d = distance_km(ride.pickup_latitude, ride.pickup_longitude, loc.latitude, loc.longitude)
            if d <= MAX_RADIUS_KM: ranked.append((d, loc.driver.user_id))
        if not ranked:
            return JsonResponse({'state':'no_driver', 'message':'No additional available drivers near your pickup.'}, headers={'Cache-Control':'no-store'})
        _, user_id = min(ranked)
        offer = RideOffer.objects.create(ride=ride, driver_id=user_id, expires_at=now+timedelta(seconds=OFFER_SECONDS))
        if ride.status == Ride.Status.REQUESTED:
            Ride.objects.filter(pk=ride.pk, status=Ride.Status.REQUESTED).update(status=Ride.Status.SEARCHING)
        return JsonResponse({'state':'offered', 'expires_at':offer.expires_at.isoformat(), 'message':'Ride offer sent to a nearby driver.'}, status=201, headers={'Cache-Control':'no-store'})


@require_GET
def offer_status(request, ride_id):
    denied = passenger(request)
    if denied is not None: return denied
    ride=Ride.objects.filter(pk=ride_id, passenger_id=request.user.pk).first()
    if not ride: return error('Ride not found.',404)
    if ride.status == Ride.Status.ASSIGNED and ride.driver_id:
        return JsonResponse({'state':'assigned', 'ride_id':ride.pk}, headers={'Cache-Control':'no-store'})
    if ride.status not in WAITING or ride.driver_id is not None: return error('Ride is no longer searching.',409)
    with transaction.atomic():
        expire(ride,timezone.now())
        pending=RideOffer.objects.filter(ride=ride,status=RideOffer.Status.PENDING).first()
    return JsonResponse({'state':'offered' if pending else 'ready', 'expires_at':pending.expires_at.isoformat() if pending else None}, headers={'Cache-Control':'no-store'})


@require_GET
def my_offer(request):
    profile, denied=driver(request)
    if denied is not None: return denied
    if profile.review_status != DriverProfile.Review.APPROVED or not profile.is_online:
        return JsonResponse({'offer':None}, headers={'Cache-Control':'no-store'})
    now=timezone.now()
    offer=RideOffer.objects.select_related('ride').filter(driver_id=request.user.pk,status=RideOffer.Status.PENDING,expires_at__gt=now,
        ride__status=Ride.Status.SEARCHING,ride__driver__isnull=True).order_by('created_at').first()
    return JsonResponse({'offer':offer_json(offer) if offer else None}, headers={'Cache-Control':'no-store'})


@require_POST
@csrf_protect
def respond(request, offer_id):
    profile, denied=driver(request)
    if denied is not None: return denied
    if request.content_type != 'application/json' or len(request.body)>256: return error('Expected JSON.',400)
    try:
        payload=json.loads(request.body)
        if not isinstance(payload,dict) or set(payload) != {'action'} or payload['action'] not in ('accept','decline'): raise ValueError()
    except (ValueError, UnicodeError, TypeError): return error('Expected accept or decline.',400)
    # Ride update is conditional, the final guard against simultaneous claims/cancellation.
    with transaction.atomic():
        offer=RideOffer.objects.select_for_update().filter(pk=offer_id,driver_id=request.user.pk).first()
        if offer is None: return error('Offer not found.',404)
        now=timezone.now()
        if offer.status != RideOffer.Status.PENDING or offer.expires_at <= now:
            if offer.status == RideOffer.Status.PENDING:
                RideOffer.objects.filter(pk=offer.pk,status=RideOffer.Status.PENDING).update(status=RideOffer.Status.EXPIRED,responded_at=now)
            return error('This offer is no longer available.',409)
        ride=Ride.objects.select_for_update().filter(pk=offer.ride_id).first()
        if ride.status not in WAITING or ride.driver_id is not None:
            RideOffer.objects.filter(pk=offer.pk,status=RideOffer.Status.PENDING).update(status=RideOffer.Status.CANCELLED,responded_at=now)
            return error('Ride is no longer available.',409)
        if payload['action'] == 'decline':
            RideOffer.objects.filter(pk=offer.pk,status=RideOffer.Status.PENDING).update(status=RideOffer.Status.DECLINED,responded_at=now)
            return JsonResponse({'state':'declined'},headers={'Cache-Control':'no-store'})
        fresh=DriverLocation.objects.filter(driver=profile, updated_at__gt=now-timedelta(seconds=LOCATION_TTL_SECONDS),accuracy_m__gte=0,accuracy_m__lte=MAX_ACCURACY_M).first()
        if profile.review_status!=DriverProfile.Review.APPROVED or not profile.is_online or not fresh:
            return error('Driver must be approved, online, and sharing fresh GPS.',403)
        if distance_km(ride.pickup_latitude,ride.pickup_longitude,fresh.latitude,fresh.longitude)>MAX_RADIUS_KM:
            return error('Driver is no longer near pickup.',409)
        if Ride.objects.filter(driver_id=request.user.pk,status__in=[Ride.Status.ASSIGNED,Ride.Status.ARRIVING,Ride.Status.ARRIVED,Ride.Status.STARTED]).exists():
            return error('Driver already has an active trip.',409)
        updated=Ride.objects.filter(pk=ride.pk,status__in=WAITING,driver__isnull=True).update(driver_id=request.user.pk,status=Ride.Status.ASSIGNED)
        if not updated: return error('Ride was claimed or cancelled.',409)
        RideOffer.objects.filter(pk=offer.pk,status=RideOffer.Status.PENDING).update(status=RideOffer.Status.ACCEPTED,responded_at=now)
    return JsonResponse({'state':'assigned','ride_id':ride.pk},headers={'Cache-Control':'no-store'})
