"""Real Geoapify autocomplete and routing. No fare/ride creation."""
import json
import math
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect

BASE = 'https://api.geoapify.com/v1/'


def _fetch(path, params):
    key = os.getenv('GEOAPIFY_API_KEY', '').strip()
    if not key:
        return None, JsonResponse({'error': 'Location service is not configured.'}, status=503)
    url = BASE + path + '?' + urlencode({**params, 'apiKey': key})
    try:
        with urlopen(Request(url, headers={'Accept': 'application/json'}), timeout=8) as response:
            return json.load(response), None
    except HTTPError as exc:
        status = 429 if exc.code == 429 else 502
        return None, JsonResponse({'error': 'Map provider request failed.'}, status=status)
    except (URLError, TimeoutError, ValueError):
        return None, JsonResponse({'error': 'Location provider temporarily unavailable.'}, status=502)


def _valid_coordinate(value, lower, upper):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value) and lower <= value <= upper


@require_GET
def location_suggestions(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)
    query = request.GET.get('q', '').strip()
    if len(query) < 3 or len(query) > 120:
        return JsonResponse({'error': 'Query must contain 3–120 characters.'}, status=400)
    data, error = _fetch('geocode/autocomplete', {
        'text': query, 'format': 'json', 'limit': 5,
        'filter': 'countrycode:ng', 'lang': 'en',
    })
    if error:
        return error
    matches = []
    for item in data.get('results', [])[:5]:
        lat, lon = item.get('lat'), item.get('lon')
        if item.get('country_code', '').lower() != 'ng':
            continue
        if not (_valid_coordinate(lat, -90, 90) and _valid_coordinate(lon, -180, 180)):
            continue
        matches.append({'label': str(item.get('formatted') or item.get('address_line1') or '')[:255], 'lat': lat, 'lon': lon})
    return JsonResponse({'results': matches})


@require_POST
@csrf_protect
def driving_route(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)
    if request.content_type != 'application/json' or len(request.body) > 4096:
        return JsonResponse({'error': 'Expected small JSON request.'}, status=400)
    try:
        payload = json.loads(request.body)
        pickup = payload['pickup']
        destination = payload['destination']
        points = [pickup, destination]
        if any(not isinstance(point, dict) for point in points):
            raise ValueError()
        if any(not (_valid_coordinate(p.get('lat'), -90, 90) and _valid_coordinate(p.get('lon'), -180, 180)) for p in points):
            raise ValueError()
        if pickup['lat'] == destination['lat'] and pickup['lon'] == destination['lon']:
            raise ValueError()
    except (ValueError, KeyError, TypeError, IndexError):
        return JsonResponse({'error': 'Enter distinct valid coordinates.'}, status=400)
    waypoints = '|'.join(f"{p['lat']},{p['lon']}" for p in points)
    data, error = _fetch('routing', {'waypoints': waypoints, 'mode': 'drive', 'format': 'json'})
    if error:
        return error
    routes = data.get('results') or []
    if not routes:
        return JsonResponse({'error': 'No drivable route found.'}, status=422)
    route = routes[0]
    try:
        meters = float(route['distance'])
        seconds = float(route['time'])
        if not (math.isfinite(meters) and math.isfinite(seconds) and meters >= 0 and seconds >= 0):
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        return JsonResponse({'error': 'Invalid route returned by provider.'}, status=502)
    return JsonResponse({'distance_m': round(meters), 'duration_s': round(seconds), 'distance_km': round(meters / 1000, 2), 'duration_min': round(seconds / 60), 'source': 'geoapify', 'fare': None})


@require_GET
def reverse_location(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)
    try:
        lat = float(request.GET.get('lat', ''))
        lon = float(request.GET.get('lon', ''))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid GPS coordinates.'}, status=400)
    if not (_valid_coordinate(lat, -90, 90) and _valid_coordinate(lon, -180, 180)):
        return JsonResponse({'error': 'Invalid GPS coordinates.'}, status=400)
    data, error = _fetch('geocode/reverse', {'lat': lat, 'lon': lon, 'format': 'json', 'lang': 'en'})
    if error:
        return error
    results = data.get('results') or []
    label = str(results[0].get('formatted') or results[0].get('address_line1') or '')[:255] if results else ''
    return JsonResponse({'label': label, 'lat': lat, 'lon': lon})
