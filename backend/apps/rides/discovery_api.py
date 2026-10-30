"""Step 41: privacy-preserving discovery, NOT dispatch or assignment."""
import math
from datetime import timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from apps.accounts.models import RiderProfile
from apps.drivers.models import DriverLocation, DriverProfile
from .models import Ride

MAX_RADIUS_KM = 5.0
MAX_ACCURACY_M = 100.0
LOCATION_TTL_SECONDS = 90

def distance_km(a,b,c,d):
    p1,p2 = math.radians(float(a)), math.radians(float(c))
    dp=p2-p1;dl=math.radians(float(d)-float(b))
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 6371.0088*2*math.asin(min(1.0,math.sqrt(max(0.0,h))))

@require_GET
def nearby_drivers(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error':'Authentication required.'},status=401)
    if not RiderProfile.objects.filter(user_id=request.user.pk,role=RiderProfile.Role.PASSENGER,phone_verified=True).exists():
        return JsonResponse({'error':'Verified passenger account required.'},status=403)
    if set(request.GET) - {'ride_id'}:
        return JsonResponse({'error':'Only ride_id is supported.'},status=400)
    try:
        ride_id=int(request.GET['ride_id'])
        if ride_id < 1: raise ValueError()
    except (KeyError,TypeError,ValueError,OverflowError):
        return JsonResponse({'error':'Valid ride_id required.'},status=400)
    ride=Ride.objects.filter(pk=ride_id,passenger_id=request.user.pk).first()
    if ride is None:
        return JsonResponse({'error':'Ride not found.'},status=404)
    if ride.status not in (Ride.Status.REQUESTED,Ride.Status.SEARCHING) or ride.driver_id is not None:
        return JsonResponse({'error':'Discovery is only available for unassigned requests.'},status=409)
    if ride.pickup_latitude is None or ride.pickup_longitude is None:
        return JsonResponse({'error':'This request has no valid pickup coordinates.'},status=422)
    now=timezone.now()
    qs=DriverLocation.objects.filter(
        driver__review_status=DriverProfile.Review.APPROVED,
        driver__is_online=True,
        driver__user__movego_profile__role=RiderProfile.Role.DRIVER,
        driver__user__movego_profile__phone_verified=True,
        updated_at__gte=now-timedelta(seconds=LOCATION_TTL_SECONDS),
        accuracy_m__gte=0,accuracy_m__lte=MAX_ACCURACY_M,
    ).values_list('latitude','longitude','accuracy_m')
    # No driver ID, coordinates, or private attributes ever returned.
    nearby=[]
    for lat,lon,accuracy in qs.iterator():
        if not all(math.isfinite(float(v)) for v in (lat,lon,accuracy)) or not (-90<=lat<=90 and -180<=lon<=180):
            continue
        dist=distance_km(ride.pickup_latitude,ride.pickup_longitude,lat,lon)
        if dist <= MAX_RADIUS_KM:
            nearby.append(dist)
    # Deliberately bucket the count rather than exposing single-driver movements.
    count=len(nearby)
    availability='none' if count==0 else 'few' if count<4 else 'several'
    return JsonResponse({'ride_id':ride.pk,'availability':availability,'search_radius_km':MAX_RADIUS_KM,
                         'location_max_age_seconds':LOCATION_TTL_SECONDS,
                         'dispatch_available':False,'message':'Driver discovery only. No driver has been assigned.'},
                         headers={'Cache-Control':'no-store'})
