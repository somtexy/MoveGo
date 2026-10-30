"""Driver onboarding and explicitly controlled availability. No driver dispatch yet."""
import io
import json
import re
import secrets

from PIL import Image, ImageOps, UnidentifiedImageError
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.models import RiderProfile
from apps.rides.models import Ride
from .models import DriverProfile, DriverLocation

FIELDS = ('first_name', 'last_name', 'nin', 'license_number', 'vehicle_make', 'vehicle_model', 'vehicle_color', 'plate_number')
DOCUMENTS = ('nin_document', 'license_photo', 'selfie_photo')
LIMITS = {'first_name': 60, 'last_name': 60, 'nin': 11, 'license_number': 64, 'vehicle_make': 60,
          'vehicle_model': 60, 'vehicle_color': 40, 'plate_number': 24}


def json_body(request, allowed):
    if request.content_type != 'application/json' or len(request.body) > 4096:
        raise ValueError('Send a small JSON request.')
    try:
        value = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        raise ValueError('Invalid JSON.')
    if not isinstance(value, dict) or set(value) != set(allowed):
        raise ValueError('Invalid request fields.')
    return value


def serialize(profile):
    return {'registered': True, 'full_name': profile.full_name, 'vehicle_make': profile.vehicle_make,
            'vehicle_model': profile.vehicle_model, 'vehicle_color': profile.vehicle_color,
            'plate_number': profile.plate_number, 'review_status': profile.review_status,
            'is_online': profile.is_online, 'dispatch_enabled': False}


def authenticated(request):
    return request.user.is_authenticated


@require_GET
def me(request):
    if not authenticated(request):
        return JsonResponse({'error': 'Login required.'}, status=401)
    driver = DriverProfile.objects.filter(user=request.user).first()
    return JsonResponse(serialize(driver) if driver else {'registered': False, 'dispatch_enabled': False})


def verified_image(upload, label):
    # Each image is checked before saving. Re-encoding removes EXIF/GPS metadata.
    if upload is None or upload.size < 100 or upload.size > 5 * 1024 * 1024:
        raise ValueError(f'{label}: choose an image smaller than 5 MB.')
    try:
        with Image.open(upload) as image:
            image.verify()
        upload.seek(0)
        with Image.open(upload) as image:
            if image.format not in ('JPEG', 'PNG', 'WEBP'):
                raise ValueError(f'{label}: JPG, PNG or WebP only.')
            width, height = image.size
            if width < 200 or height < 200 or width * height > 20000000:
                raise ValueError(f'{label}: image resolution is invalid.')
            image = ImageOps.exif_transpose(image).convert('RGB')
            image.thumbnail((2000, 2000))
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=84, optimize=True)
            return ContentFile(output.getvalue(), name=f'{secrets.token_hex(20)}.jpg')
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValueError(f'{label}: file is not a valid image.')


@require_POST
@csrf_protect
def register(request):
    if not authenticated(request):
        return JsonResponse({'error': 'Login required.'}, status=401)
    if not request.content_type.startswith('multipart/form-data'):
        return JsonResponse({'error': 'Submit the form with your document photos.'}, status=400)
    if request.META.get('CONTENT_LENGTH') and int(request.META['CONTENT_LENGTH']) > 16 * 1024 * 1024:
        return JsonResponse({'error': 'Application files are too large.'}, status=413)
    try:
        if set(request.POST.keys()) != set(FIELDS) or set(request.FILES.keys()) != set(DOCUMENTS):
            raise ValueError('Complete all required details and upload all three photos.')
        cleaned = {}
        for key in FIELDS:
            val = ' '.join(request.POST[key].strip().split())
            if not (2 <= len(val) <= LIMITS[key]) or any(ord(c) < 32 for c in val):
                raise ValueError(f'Invalid {key.replace("_", " ")}.')
            cleaned[key] = val
        if not re.fullmatch(r'\d{11}', cleaned['nin']):
            raise ValueError('NIN must be exactly 11 digits.')
        if not re.fullmatch(r'[A-Za-z0-9 -]{3,24}', cleaned['plate_number']):
            raise ValueError('Enter a valid vehicle plate number.')
        images = {k: verified_image(request.FILES.get(k), k.replace('_', ' ')) for k in DOCUMENTS}
    except (ValueError, KeyError, TypeError) as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    with transaction.atomic():
        rp = RiderProfile.objects.select_for_update().filter(user=request.user).first()
        if rp is None or not rp.phone_verified:
            return JsonResponse({'error': 'Verify your phone before registering as a driver.'}, status=403)
        if DriverProfile.objects.filter(user=request.user).exists():
            return JsonResponse({'error': 'Driver application already submitted.'}, status=409)
        if Ride.objects.filter(passenger=request.user, status__in=[
            Ride.Status.REQUESTED, Ride.Status.SEARCHING, Ride.Status.ASSIGNED,
            Ride.Status.ARRIVING, Ride.Status.ARRIVED, Ride.Status.STARTED,
        ]).exists():
            return JsonResponse({'error': 'Complete or cancel your active passenger request first.'}, status=409)
        profile = DriverProfile.objects.create(
            user=request.user, full_name=f'{cleaned["first_name"]} {cleaned["last_name"]}',
            **cleaned,
        )
        for key, content in images.items():
            getattr(profile, key).save(content.name, content, save=False)
        profile.save()
        rp.role = RiderProfile.Role.DRIVER
        rp.save(update_fields=['role'])
    return JsonResponse(serialize(profile), status=201)


@staff_member_required
@require_GET
def review_document(request, profile_id, kind):
    # Never expose document URLs through MEDIA_URL, the frontend directory or the driver API.
    if not request.user.has_perm('drivers.view_driverprofile'):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    if kind not in DOCUMENTS:
        raise Http404()
    profile = DriverProfile.objects.filter(pk=profile_id).first()
    if not profile:
        raise Http404()
    document = getattr(profile, kind)
    if not document:
        raise Http404()
    try:
        return FileResponse(document.open('rb'), content_type='image/jpeg', as_attachment=False,
                            filename=f'driver-{profile.pk}-{kind}.jpg',
                            headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})
    except FileNotFoundError:
        raise Http404()


@require_POST
@csrf_protect
def availability(request):
    if not authenticated(request):
        return JsonResponse({'error': 'Login required.'}, status=401)
    try:
        data = json_body(request, ('is_online',))
        if type(data['is_online']) is not bool:
            raise ValueError('is_online must be true or false.')
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    with transaction.atomic():
        profile = DriverProfile.objects.select_for_update().filter(user=request.user).first()
        rp = RiderProfile.objects.filter(user=request.user, role=RiderProfile.Role.DRIVER, phone_verified=True).first()
        if profile is None or rp is None:
            return JsonResponse({'error': 'Registered, phone-verified driver required.'}, status=403)
        if data['is_online'] and profile.review_status != DriverProfile.Review.APPROVED:
            return JsonResponse({'error': 'Driver application must be approved before going online.'}, status=403)
        profile.is_online = data['is_online'] if profile.review_status == DriverProfile.Review.APPROVED else False
        profile.save(update_fields=['is_online', 'updated_at'])
        if not profile.is_online:
            DriverLocation.objects.filter(driver=profile).delete()
    return JsonResponse(serialize(profile))
