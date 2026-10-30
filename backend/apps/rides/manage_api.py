"""Passenger-owned request management. No dispatch, refunds, or driver cancellation."""
import json
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from apps.accounts.models import RiderProfile
from .models import Ride

CANCELLABLE = (Ride.Status.REQUESTED, Ride.Status.SEARCHING)
ACTIVE = (Ride.Status.REQUESTED, Ride.Status.SEARCHING, Ride.Status.ASSIGNED,
          Ride.Status.ARRIVING, Ride.Status.ARRIVED, Ride.Status.STARTED)


def _passenger_error(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)
    if not RiderProfile.objects.filter(user_id=request.user.pk, role=RiderProfile.Role.PASSENGER, phone_verified=True).exists():
        return JsonResponse({'error': 'Verified passenger account required.'}, status=403)
    return None


def _serialize(ride):
    return {'id': ride.pk, 'status': ride.status, 'pickup': ride.pickup_label,
            'destination': ride.destination_label, 'category': ride.category,
            'estimated_fare_kobo': ride.estimated_fare_kobo,
            'created_at': ride.created_at.isoformat(),
            'can_cancel': ride.status in CANCELLABLE and ride.driver_id is None}


@require_GET
def active_request(request):
    error = _passenger_error(request)
    if error is not None:
        return error
    ride = Ride.objects.filter(passenger_id=request.user.pk, status__in=ACTIVE).order_by('-created_at', '-id').first()
    return JsonResponse({'ride': _serialize(ride) if ride else None,
                         'dispatch_available': False})


@require_POST
@csrf_protect
def cancel_request(request, ride_id):
    error = _passenger_error(request)
    if error is not None:
        return error
    if request.content_type != 'application/json' or len(request.body) > 1024:
        return JsonResponse({'error': 'A JSON request is required.'}, status=400)
    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeError):
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    if payload != {}:
        return JsonResponse({'error': 'No cancellation fields are accepted.'}, status=400)
    with transaction.atomic():
        ride = Ride.objects.select_for_update().filter(pk=ride_id, passenger_id=request.user.pk).first()
        if ride is None:
            return JsonResponse({'error': 'Ride request not found.'}, status=404)
        if ride.status == Ride.Status.CANCELLED:
            return JsonResponse({'ride': _serialize(ride), 'message': 'Already cancelled.'})
        if ride.status not in CANCELLABLE or ride.driver_id is not None:
            return JsonResponse({'error': 'This trip can no longer be cancelled here.'}, status=409)
        # Conditional update also prevents overwriting a concurrent status transition.
        changed = Ride.objects.filter(pk=ride.pk, passenger_id=request.user.pk,
                                      driver__isnull=True, status__in=CANCELLABLE).update(status=Ride.Status.CANCELLED)
        if not changed:
            return JsonResponse({'error': 'Ride status changed. Please refresh.'}, status=409)
        ride.refresh_from_db()
    return JsonResponse({'ride': _serialize(ride), 'message': 'Request cancelled. No payment was collected.'})
