from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Ride(models.Model):
    """Future server-created trip record. Never trust frontend price or status."""

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        SEARCHING = "searching", "Searching"
        ASSIGNED = "assigned", "Driver assigned"
        ARRIVING = "arriving", "Driver arriving"
        ARRIVED = "arrived", "Driver arrived"
        STARTED = "started", "Trip started"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    passenger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="passenger_rides")
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="driver_rides", null=True, blank=True)
    pickup_label = models.CharField(max_length=255)
    destination_label = models.CharField(max_length=255)
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destination_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destination_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    category = models.CharField(max_length=30)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.REQUESTED, db_index=True)
    # These are backend-controlled snapshots; no fare is guessed or set by browser yet.
    estimated_fare_kobo = models.PositiveBigIntegerField(null=True, blank=True)
    final_fare_kobo = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.CheckConstraint(condition=Q(driver__isnull=True) | ~Q(passenger=models.F("driver")), name="movego_driver_not_passenger"),
        ]

    def __str__(self):
        return f"Ride {self.pk} ({self.status})"

# Register Step 42 dispatch model with the Django app registry.
from .offer_models import RideOffer

# Register Step 44 payment model with Django
from .payment_models import RidePayment
