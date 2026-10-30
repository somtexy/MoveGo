"""Require recent, session-bound app PIN verification for sensitive updates."""
from datetime import timedelta
from django.utils import timezone
from .pin_models import AppPIN

SESSION_KEY = 'movego_pin_recently_verified'
WINDOW_SECONDS = 300


def mark_verified(request):
    request.session[SESSION_KEY] = {'user_id': request.user.pk, 'at': int(timezone.now().timestamp())}
    request.session.modified = True


def clear_verified(request):
    request.session.pop(SESSION_KEY, None)


def has_fresh_confirmation(request):
    if not request.user.is_authenticated:
        return False
    proof = request.session.get(SESSION_KEY)
    if not isinstance(proof, dict) or proof.get('user_id') != request.user.pk:
        return False
    when = proof.get('at')
    if not isinstance(when, int):
        return False
    age = timezone.now().timestamp() - when
    return 0 <= age <= WINDOW_SECONDS


def needs_pin(request):
    return AppPIN.objects.filter(user=request.user).exists()
