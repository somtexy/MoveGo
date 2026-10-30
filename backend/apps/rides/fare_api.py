"""MoveGo starter-tariff quotes. Rates are illustrative until approved by operator."""
import json
import math
from decimal import Decimal, ROUND_HALF_UP
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from .location_api import _fetch, _valid_coordinate

# Example pricing only: (base in NGN, per km NGN, per min NGN, minimum NGN).
# Review real operating costs and approve tariffs before accepting bookings.
TARIFFS = {
    "Ride": (800, 220, 35, 1200),
    "Comfort": (1400, 310, 50, 2100),
    "One Click": (950, 250, 40, 1500),
    "Couriers": (700, 190, 30, 1100),
}


def quote_amount_kobo(base, per_km, per_min, minimum, distance_m, duration_s):
    km = Decimal(str(distance_m)) / Decimal("1000")
    minutes = Decimal(str(duration_s)) / Decimal("60")
    fare = Decimal(base) + Decimal(per_km) * km + Decimal(per_min) * minutes
    return int((max(fare, Decimal(minimum)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@require_POST
@csrf_protect
def fare_quotes(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    if request.content_type != "application/json" or len(request.body) > 4096:
        return JsonResponse({"error": "Expected a small JSON request"}, status=400)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict) or set(payload) != {"pickup", "destination"}:
            raise ValueError()
        points = [payload["pickup"], payload["destination"]]
        if any(not isinstance(p, dict) or not
               (_valid_coordinate(p.get("lat"), -90, 90) and
                _valid_coordinate(p.get("lon"), -180, 180)) for p in points):
            raise ValueError()
        if points[0]["lat"] == points[1]["lat"] and points[0]["lon"] == points[1]["lon"]:
            raise ValueError()
    except (ValueError, TypeError, KeyError, UnicodeError):
        return JsonResponse({"error": "Choose distinct valid coordinates"}, status=400)

    waypoints = "|".join(f"{p['lat']},{p['lon']}" for p in points)
    data, error = _fetch("routing", {"waypoints": waypoints, "mode": "drive", "format": "json"})
    if error is not None:
        return error
    try:
        route = data["results"][0]
        distance = float(route["distance"])
        duration = float(route["time"])
        if not (math.isfinite(distance) and math.isfinite(duration) and
                0 < distance <= 300000 and 0 < duration <= 86400):
            raise ValueError()
    except (KeyError, TypeError, ValueError, IndexError):
        return JsonResponse({"error": "Unable to calculate a valid road route"}, status=422)

    quotes = [{
        "category": name,
        "estimated_fare_kobo": quote_amount_kobo(*rates, distance, duration),
        "currency": "NGN",
    } for name, rates in TARIFFS.items()]
    return JsonResponse({
        "distance_m": round(distance),
        "duration_s": round(duration),
        "distance_km": round(distance / 1000, 2),
        "duration_min": round(duration / 60),
        "quotes": quotes,
        "pricing_status": "starter_tariffs_not_live",
        "disclaimer": "Illustrative MoveGo starter tariffs; not a bookable fare.",
        "source": "geoapify",
    })
