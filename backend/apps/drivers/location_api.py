"""Step 35. Authenticated private location ingestion; no public driver lookup."""
import json
import math
from datetime import timedelta
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from apps.accounts.models import RiderProfile
from .models import DriverLocation, DriverProfile

LOCATION_TTL_SECONDS = 90
MAX_REQUEST_BYTES = 1024


def permitted_driver(request):
    if not request.user.is_authenticated:
        return None, 401
    profile = DriverProfile.objects.filter(user=request.user).first()
    if not profile or not RiderProfile.objects.filter(user=request.user, role=RiderProfile.Role.DRIVER, phone_verified=True).exists():
        return None, 403
    if profile.review_status != DriverProfile.Review.APPROVED or not profile.is_online:
        return None, 403
    return profile, 200


@require_GET
def location_status(request):
    profile, code = permitted_driver(request)
    if profile is None:
        return JsonResponse({'error': 'Approved online driver required.' if code == 403 else 'Login required.'}, status=code)
    point = DriverLocation.objects.filter(driver=profile).first()
    if not point:
        return JsonResponse({'sharing_active': False, 'fresh': False, 'last_update': None})
    fresh = point.updated_at >= timezone.now() - timedelta(seconds=LOCATION_TTL_SECONDS)
    # Do not return precise coordinates; only the driver can upload a new position.
    return JsonResponse({'sharing_active': fresh, 'fresh': fresh, 'last_update': point.updated_at.isoformat(),
                         'accuracy_m': point.accuracy_m if fresh else None})


@require_POST
@csrf_protect
def update_location(request):
    profile, code = permitted_driver(request)
    if profile is None:
        return JsonResponse({'error': 'Approved online driver required.' if code == 403 else 'Login required.'}, status=code)
    if request.content_type != 'application/json' or len(request.body) > MAX_REQUEST_BYTES:
        return JsonResponse({'error': 'Expected a small JSON request.'}, status=400)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict) or set(payload) != {'lat', 'lon', 'accuracy_m'}:
            raise ValueError()
        values = [payload['lat'], payload['lon'], payload['accuracy_m']]
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in values):
            raise ValueError()
        lat, lon, accuracy = (float(x) for x in values)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and 0 <= accuracy <= 2000):
            raise ValueError()
    except (ValueError, TypeError, KeyError, OverflowError):
        return JsonResponse({'error': 'Invalid GPS coordinates or accuracy.'}, status=400)
    with transaction.atomic():
        # Lock profile to serialize location writes with availability changes.
        locked = DriverProfile.objects.select_for_update().get(pk=profile.pk)
        if locked.review_status != DriverProfile.Review.APPROVED or not locked.is_online:
            return JsonResponse({'error': 'Driver is no longer online and approved.'}, status=403)
        point, _ = DriverLocation.objects.update_or_create(driver=locked, defaults={
            'latitude': lat, 'longitude': lon, 'accuracy_m': accuracy,
        })
    return JsonResponse({'saved': True, 'updated_at': point.updated_at.isoformat()})


@require_POST
@csrf_protect
def stop_location(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required.'}, status=401)
    # Let a driver stop sharing even if approval was revoked or they went offline.
    with transaction.atomic():
        profile = DriverProfile.objects.select_for_update().filter(user=request.user).first()
        if not profile:
            return JsonResponse({'error': 'Driver account required.'}, status=403)
        DriverLocation.objects.filter(driver=profile).delete()
    return JsonResponse({'sharing_active': False, 'stopped': True})
