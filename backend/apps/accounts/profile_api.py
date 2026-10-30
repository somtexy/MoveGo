
"""Authenticated MoveGo passenger profile read/update API."""

import json
import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from .models import RiderProfile
from .pin_guard import needs_pin, has_fresh_confirmation


NAME_RE = re.compile(r"^[^\W\d_][\w .'-]*$", re.UNICODE)


def details(user):
    profile = RiderProfile.objects.filter(user=user).first()

    return {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email or "",
        "phone": profile.phone if profile else "",
        "phone_verified": bool(
            profile and profile.phone_verified
        ),
        "role": profile.role if profile else "passenger",
    }


@require_http_methods(["GET", "PATCH"])
@csrf_protect
def profile_detail(request):

    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Authentication required"},
            status=401
        )

    if request.method == "GET":
        return JsonResponse({
            "profile": details(request.user)
        })

    if request.content_type != "application/json":
        return JsonResponse(
            {"error": "Expected JSON"},
            status=400
        )

    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeError):
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400
        )

    if (
        not isinstance(data, dict)
        or set(data) != {"first_name", "last_name", "email"}
    ):
        return JsonResponse(
            {
                "error": (
                    "Submit first_name, last_name and email"
                )
            },
            status=400
        )

    if any(not isinstance(data[k], str) for k in data):
        return JsonResponse(
            {"error": "All profile fields must be text"},
            status=400
        )

    first = " ".join(data["first_name"].split())
    last = " ".join(data["last_name"].split())
    email = data["email"].strip().lower()

    # Validate first name
    if not (
        2 <= len(first) <= 50
        and NAME_RE.fullmatch(first)
    ):
        return JsonResponse(
            {
                "error": (
                    "Enter a valid first name (2–50 characters)"
                )
            },
            status=400
        )

    # Validate last name
    if last and not (
        len(last) <= 50
        and NAME_RE.fullmatch(last)
    ):
        return JsonResponse(
            {"error": "Enter a valid last name"},
            status=400
        )

    # Validate email length
    if len(email) > 254:
        return JsonResponse(
            {"error": "Email address is too long"},
            status=400
        )

    # Validate email format
    if email:
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse(
                {"error": "Enter a valid email address"},
                status=400
            )

    # Get the actual Django user model
    User = get_user_model()

    # Check whether the email is already used
    if email and User.objects.filter(
        email__iexact=email
    ).exclude(
        pk=request.user.pk
    ).exists():
        return JsonResponse(
            {
                "error": (
                    "Email already used by another account"
                )
            },
            status=409
        )

    # Save changes to Django database
    # Changing the email address requires a recently verified App PIN.
    if (email != (request.user.email or '').strip().lower()
            and needs_pin(request) and not has_fresh_confirmation(request)):
        return JsonResponse({
            'error': 'Verify your App PIN before changing your email.',
            'code': 'PIN_CONFIRMATION_REQUIRED',
            'pin_url': '/app/passenger/passkey.html',
        }, status=403)

    with transaction.atomic():

        user = User.objects.select_for_update().get(
            pk=request.user.pk
        )

        if email and User.objects.filter(
            email__iexact=email
        ).exclude(
            pk=user.pk
        ).exists():
            return JsonResponse(
                {
                    "error": (
                        "Email already used by another account"
                    )
                },
                status=409
            )

        user.first_name = first
        user.last_name = last
        user.email = email

        user.save(
            update_fields=[
                "first_name",
                "last_name",
                "email"
            ]
        )

    return JsonResponse({
        "profile": details(user),
        "message": "Profile saved"
    })
