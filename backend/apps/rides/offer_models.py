from django.conf import settings
from django.db import models
from django.db.models import Q


class RideOffer(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
        EXPIRED = 'expired', 'Expired'
        CANCELLED = 'cancelled', 'Cancelled'

    ride = models.ForeignKey('rides.Ride', related_name='dispatch_offers', on_delete=models.CASCADE)
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_ride_offers', on_delete=models.PROTECT)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['ride'], condition=Q(status='pending'), name='movego_one_pending_offer_per_ride'),
            models.UniqueConstraint(fields=['ride', 'driver'], name='movego_one_offer_per_driver_per_ride'),
        ]
