from django.conf import settings
from django.db import models
from django.core.files.storage import FileSystemStorage
from pathlib import Path


def private_driver_storage():
    """Never expose KYC photos via public MEDIA_URL."""
    root = getattr(settings, "PRIVATE_DRIVER_MEDIA_ROOT", Path(settings.BASE_DIR) / "private_driver_uploads")
    return FileSystemStorage(location=root, base_url=None)


class DriverProfile(models.Model):
    class Review(models.TextChoices):
        PENDING = 'pending', 'Pending review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='driver_profile')
    full_name = models.CharField(max_length=120)  # Keep compatibility with Step 34.
    first_name = models.CharField(max_length=60, blank=True)
    last_name = models.CharField(max_length=60, blank=True)
    nin = models.CharField(max_length=11, blank=True)
    nin_document = models.FileField(upload_to='driver_docs/nin/', storage=private_driver_storage, blank=True)
    license_photo = models.FileField(upload_to='driver_docs/license/', storage=private_driver_storage, blank=True)
    selfie_photo = models.FileField(upload_to='driver_docs/selfie/', storage=private_driver_storage, blank=True)
    license_number = models.CharField(max_length=64)
    vehicle_make = models.CharField(max_length=60)
    vehicle_model = models.CharField(max_length=60)
    vehicle_color = models.CharField(max_length=40)
    plate_number = models.CharField(max_length=24)
    review_status = models.CharField(max_length=12, choices=Review.choices, default=Review.PENDING)
    is_online = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Driver {self.user_id}: {self.review_status}'


class DriverLocation(models.Model):
    """Latest driver GPS position only; not a trip/location history."""
    driver = models.OneToOneField(DriverProfile, on_delete=models.CASCADE, related_name='latest_location')
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy_m = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Private location for driver #{self.driver_id}'
