"""Authenticated, server-authoritative trip transitions (MoveGo Step 43)."""
import json
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from apps.accounts.models import RiderProfile
from apps.drivers.models import DriverProfile
from .models import Ride

TRANSITIONS = {
    Ride.Status.ASSIGNED: ("depart", Ride.Status.ARRIVING),
    Ride.Status.ARRIVING: ("arrive", Ride.Status.ARRIVED),
    Ride.Status.ARRIVED: ("start", Ride.Status.STARTED),
    Ride.Status.STARTED: ("complete", Ride.Status.COMPLETED),
}
ACTIVE = (Ride.Status.ASSIGNED, Ride.Status.ARRIVING, Ride.Status.ARRIVED, Ride.Status.STARTED)

def fail(msg, status):
    return JsonResponse({"error":msg}, status=status, headers={"Cache-Control":"no-store"})

def allowed(request):
    if not request.user.is_authenticated:
        return fail('Authentication required.', 401)
    if not RiderProfile.objects.filter(user=request.user, phone_verified=True).exists():
        return fail('Verified account required.', 403)
    return None

def public_data(ride):
    return {'ride_id':ride.pk, 'status':ride.status, 'pickup':ride.pickup_label,
            'destination':ride.destination_label, 'category':ride.category,
            'estimated_fare_kobo':ride.estimated_fare_kobo,
            'final_fare_kobo':ride.final_fare_kobo,
            'payment_status':'not_implemented'}

@require_GET
def my_trip(request):
    blocked=allowed(request)
    if blocked is not None: return blocked
    qs=Ride.objects.filter(status__in=ACTIVE)
    is_driver=RiderProfile.objects.filter(user=request.user,role=RiderProfile.Role.DRIVER).exists()
    qs=qs.filter(driver_id=request.user.pk) if is_driver else qs.filter(passenger_id=request.user.pk)
    ride=qs.order_by('-created_at').first()
    return JsonResponse({'ride':public_data(ride) if ride else None},headers={'Cache-Control':'no-store'})

@require_GET
def trip_status(request, ride_id):
    blocked=allowed(request)
    if blocked is not None: return blocked
    ride=Ride.objects.filter(pk=ride_id).first()
    if ride is None or request.user.pk not in (ride.passenger_id,ride.driver_id):
        return fail('Trip not found.',404)
    return JsonResponse({'ride':public_data(ride)},headers={'Cache-Control':'no-store'})

@require_POST
@csrf_protect
def advance_trip(request, ride_id):
    blocked=allowed(request)
    if blocked is not None: return blocked
    if request.content_type!='application/json' or len(request.body)>256:
        return fail('Expected JSON.',400)
    try:
        payload=json.loads(request.body)
    except (ValueError,UnicodeError):
        return fail('Invalid JSON.',400)
    if not isinstance(payload,dict) or set(payload)!={'action'} or payload['action'] not in ('depart','arrive','start','complete'):
        return fail('Invalid trip action.',400)
    if not RiderProfile.objects.filter(user=request.user,role=RiderProfile.Role.DRIVER).exists():
        return fail('Driver account required.',403)
    with transaction.atomic():
        ride=Ride.objects.select_for_update().filter(pk=ride_id,driver_id=request.user.pk).first()
        if ride is None: return fail('Trip not found.',404)
        expected=TRANSITIONS.get(ride.status)
        if expected is None or payload['action']!=expected[0]:
            return fail('Invalid trip state transition.',409)
        updated=Ride.objects.filter(pk=ride.pk,driver_id=request.user.pk,status=ride.status).update(status=expected[1])
        if updated!=1:return fail('Trip already changed.',409)
        ride.status=expected[1]
    return JsonResponse({'ride':public_data(ride)},headers={'Cache-Control':'no-store'})
