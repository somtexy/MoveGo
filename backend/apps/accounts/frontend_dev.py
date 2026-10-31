"""Local-only, explicitly allowlisted frontend asset server for Django DEBUG."""
import mimetypes
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET


FRONTEND_ROOT = (settings.BASE_DIR.parent / "frontend").resolve()
ALLOWED_ROOTS = {"passenger", "driver", "admin", "css", "js", "assets", 'videos'}
ALLOWED_SUFFIXES = {".html", ".css", ".js", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".json", ".woff", ".woff2", '.mp4'}



@require_GET
def frontend_asset(request, asset_path):
    
    if asset_path.split("/", 1)[0] not in ALLOWED_ROOTS:
        raise Http404()
    file_path = (FRONTEND_ROOT / asset_path).resolve()
    if not file_path.is_relative_to(FRONTEND_ROOT) or not file_path.is_file() or file_path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise Http404()
    content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    response = FileResponse(file_path.open("rb"), content_type=content_type)
    response["Cache-Control"] = "no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
