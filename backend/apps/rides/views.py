from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.accounts.models import RiderProfile
from .models import Ride


@require_GET
def passenger_ride_history(request):
    """Real DB records only. No fabricated demo trips or client-side history."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    passenger = RiderProfile.objects.filter(
        user_id=request.user.pk, role=RiderProfile.Role.PASSENGER,
        phone_verified=True,
    ).exists()
    if not passenger:
        return JsonResponse({"error": "Verified passenger account required"}, status=403)

    rides = Ride.objects.filter(passenger_id=request.user.pk).order_by("-created_at", "-id")[:50]
    return JsonResponse({"rides": [
        {
            "id": ride.pk,
            "pickup": ride.pickup_label,
            "destination": ride.destination_label,
            "category": ride.category,
            "status": ride.status,
            "estimated_fare_kobo": ride.estimated_fare_kobo,
            "final_fare_kobo": ride.final_fare_kobo,
            "created_at": ride.created_at.isoformat(),
        }
        for ride in rides
    ]})
