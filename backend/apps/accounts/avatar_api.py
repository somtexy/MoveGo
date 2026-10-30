"""Private, authenticated, bounded image upload and display for MoveGo account avatars."""
import io
import secrets
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from .avatar_models import AccountAvatar

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_PIXEL_COUNT = 16_000_000
MAX_SIDE = 512

def _directory():
    # Not in FRONTEND_ROOT, STATIC_ROOT or MEDIA_ROOT: never served publicly.
    root = Path(settings.BASE_DIR) / 'private_user_avatars'
    root.mkdir(parents=True, exist_ok=True)
    return root

def _record(user):
    return AccountAvatar.objects.filter(user=user).first()

def _error(message, code):
    return JsonResponse({'error': message}, status=code)


def _unlink_if_unlocked(path):
    """Delete superseded private photo if no reader holds it open on Windows.

    A pending Windows FileResponse reader may retain a handle. A private orphan
    is preferable to a failed user update; cleanup can be retried later.
    """
    try:
        path.unlink(missing_ok=True)
    except PermissionError:
        pass

@require_http_methods(['GET', 'POST', 'DELETE'])
@csrf_protect
def avatar_detail(request):
    if not request.user.is_authenticated:
        return _error('Authentication required', 401)
    if request.method == 'GET':
        record = _record(request.user)
        if not record:
            return _error('No profile photo', 404)
        file = _directory() / record.filename
        try:
            handle = open(file, 'rb')
        except OSError:
            return _error('Profile photo unavailable', 404)
        response = FileResponse(handle, content_type='image/webp')
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    if request.method == 'DELETE':
        with transaction.atomic():
            old = AccountAvatar.objects.select_for_update().filter(user=request.user).first()
            old_name = old.filename if old else None
            if old: old.delete()
        if old_name: _unlink_if_unlocked(_directory() / old_name)
        return JsonResponse({'has_photo': False, 'message': 'Profile photo removed'})
    photo = request.FILES.get('photo')
    if photo is None or len(request.FILES) != 1:
        return _error('Select one photo to upload', 400)
    if photo.size > MAX_FILE_BYTES or photo.size == 0:
        return _error('Photo must be under 5 MB', 400)
    # Limit both input bytes and decoded pixel count; never save raw untrusted bytes.
    try:
        contents = photo.read(MAX_FILE_BYTES + 1)
        if len(contents) > MAX_FILE_BYTES:
            return _error('Photo must be under 5 MB', 400)
        with Image.open(io.BytesIO(contents)) as im:
            if im.format not in ('JPEG', 'PNG', 'WEBP'):
                return _error('Use JPG, PNG or WebP', 400)
            if im.width * im.height > MAX_PIXEL_COUNT:
                return _error('Image dimensions are too large', 400)
            im = ImageOps.exif_transpose(im)
            im = im.convert('RGB')
            im.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            im.save(buffer, format='WEBP', quality=82, method=5)
            encoded = buffer.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        return _error('Invalid image', 400)
    filename = secrets.token_hex(24) + '.webp'
    path = _directory() / filename
    # Exclusive creation; random names prevent conflicts and guessing.
    with path.open('xb') as handle:
        handle.write(encoded)
    try:
        with transaction.atomic():
            record = AccountAvatar.objects.select_for_update().filter(user=request.user).first()
            old_name = record.filename if record else None
            if record:
                record.filename = filename
                record.save(update_fields=['filename', 'updated_at'])
            else:
                AccountAvatar.objects.create(user=request.user, filename=filename)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    if old_name: _unlink_if_unlocked(_directory() / old_name)
    return JsonResponse({'has_photo': True, 'message': 'Profile photo updated'})
