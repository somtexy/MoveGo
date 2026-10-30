from django.conf import settings
from django.db import models

class AccountAvatar(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="movego_avatar")
    filename = models.CharField(max_length=64)
    updated_at = models.DateTimeField(auto_now=True)
