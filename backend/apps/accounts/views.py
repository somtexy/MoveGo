import json
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from .models import RiderProfile

User = get_user_model()


def payload(request):
    if request.content_type != "application/json":
        return None
    try:
        value = json.loads(request.body)
        return value if isinstance(value, dict) else None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def public_user(user):
    profile = getattr(user, "movego_profile", None)
    return {"id": user.pk, "email": user.email, "first_name": user.first_name,
            "last_name": user.last_name, "role": profile.role if profile else "passenger",
            "phone_verified": profile.phone_verified if profile else False}


@require_GET
@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})


@require_POST
@csrf_protect
def register(request):
    data = payload(request)
    if data is None:
        return error("Expected a JSON object")
    email = str(data.get("email", "")).strip().lower()
    first_name = str(data.get("first_name", "")).strip()
    password = data.get("password", "")
    role = data.get("role", "passenger")
    if not email or len(email) > 254 or "@" not in email:
        return error("Enter a valid email address")
    if not first_name or len(first_name) > 150:
        return error("First name is required (maximum 150 characters)")
    if role not in ("passenger", "driver"):
        return error("Invalid account role")
    if not isinstance(password, str):
        return error("Password is required")
    user = User(username=email, email=email, first_name=first_name)
    try:
        validate_password(password, user=user)
    except ValidationError as exc:
        return JsonResponse({"errors": exc.messages}, status=400)
    if User.objects.filter(username__iexact=email).exists():
        return error("An account with this email already exists", 409)
    try:
        with transaction.atomic():
            user.set_password(password)
            user.save()
            RiderProfile.objects.create(user=user, role=role)
    except IntegrityError:
        return error("An account with this email already exists", 409)
    login(request, user)
    return JsonResponse({"user": public_user(user)}, status=201)


@require_POST
@csrf_protect
def sign_in(request):
    data = payload(request)
    if data is None:
        return error("Expected a JSON object")
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")
    if not isinstance(password, str):
        return error("Invalid email or password", 401)
    user = authenticate(request, username=email, password=password)
    if user is None or not user.is_active:
        return error("Invalid email or password", 401)
    login(request, user)
    return JsonResponse({"user": public_user(user)})


@require_POST
@csrf_protect
def sign_out(request):
    logout(request)
    return JsonResponse({"status": "signed_out"})


@require_GET
def me(request):
    if not request.user.is_authenticated:
        return error("Authentication required", 401)
    return JsonResponse({"user": public_user(request.user)})
