"""Persist a passenger ride request without pretending dispatch or payment exists."""
import json
import math
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from apps.accounts.models import RiderProfile
from .fare_api import TARIFFS, quote_amount_kobo
from .location_api import _fetch, _valid_coordinate
from .models import Ride


@require_POST
@csrf_protect
def create_ride_request(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)
    if not RiderProfile.objects.filter(
        user_id=request.user.pk, role=RiderProfile.Role.PASSENGER, phone_verified=True
    ).exists():
        return JsonResponse({"error": "Verified passenger account required."}, status=403)
    if request.content_type != "application/json" or len(request.body) > 4096:
        return JsonResponse({"error": "A small JSON request is required."}, status=400)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict) or set(payload) != {"pickup", "destination", "category", "payment_method"}:
            raise ValueError
        category = payload["category"]
        if not isinstance(category, str) or category not in TARIFFS:
            raise ValueError
        # No payments have been implemented. Never accept a paid/online booking.
        if payload["payment_method"] != "cash":
            return JsonResponse({"error": "Online payments are not available yet. Choose cash."}, status=422)
        places = [payload["pickup"], payload["destination"]]
        for place in places:
            if not isinstance(place, dict) or set(place) != {"label", "lat", "lon"}:
                raise ValueError
            if not isinstance(place["label"], str) or not 3 <= len(place["label"].strip()) <= 255:
                raise ValueError
            if not (_valid_coordinate(place["lat"], -90, 90) and _valid_coordinate(place["lon"], -180, 180)):
                raise ValueError
        if (places[0]["lat"], places[0]["lon"]) == (places[1]["lat"], places[1]["lon"]):
            raise ValueError
    except (ValueError, TypeError, KeyError, UnicodeError):
        return JsonResponse({"error": "Choose a category and two valid, distinct locations."}, status=400)

    # Recalculate the actual route and fare on the server. Browser quote is ignored.
    waypoints = "|".join(f'{p["lat"]},{p["lon"]}' for p in places)
    route_data, provider_error = _fetch("routing", {"waypoints": waypoints, "mode": "drive", "format": "json"})
    if provider_error is not None:
        return provider_error
    try:
        route = route_data["results"][0]
        distance = float(route["distance"])
        duration = float(route["time"])
        if not (math.isfinite(distance) and math.isfinite(duration) and 0 < distance <= 300000 and 0 < duration <= 86400):
            raise ValueError
    except (TypeError, ValueError, IndexError, KeyError):
        return JsonResponse({"error": "Could not validate the driving route."}, status=422)

    estimated_kobo = quote_amount_kobo(*TARIFFS[category], distance, duration)
    with transaction.atomic():
        # Serialize submissions per passenger on databases supporting row locking.
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        existing = Ride.objects.filter(
            passenger_id=request.user.pk,
            status__in=[Ride.Status.REQUESTED, Ride.Status.SEARCHING, Ride.Status.ASSIGNED,
                        Ride.Status.ARRIVING, Ride.Status.ARRIVED, Ride.Status.STARTED],
        ).first()
        if existing:
            return JsonResponse({"error": "You already have an active ride request.", "ride_id": existing.pk}, status=409)
        ride = Ride.objects.create(
            passenger=request.user,
            pickup_label=places[0]["label"].strip(),
            destination_label=places[1]["label"].strip(),
            pickup_latitude=Decimal(str(places[0]["lat"])),
            pickup_longitude=Decimal(str(places[0]["lon"])),
            destination_latitude=Decimal(str(places[1]["lat"])),
            destination_longitude=Decimal(str(places[1]["lon"])),
            category=category,
            status=Ride.Status.REQUESTED,
            estimated_fare_kobo=estimated_kobo,
        )
    return JsonResponse({
        "ride_id": ride.pk,
        "status": ride.status,
        "estimated_fare_kobo": estimated_kobo,
        "currency": "NGN",
        "pricing_status": "starter_tariffs_not_live",
        "dispatch_status": "unavailable",
        "message": "Ride request saved. No driver search or assignment is active yet. This is not a confirmed booking.",
    }, status=201)
