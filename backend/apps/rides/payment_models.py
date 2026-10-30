"""A single test-mode payment record per ride; authoritative amounts are server-owned."""
from django.db import models
from django.conf import settings

class RidePayment(models.Model):
    class Method(models.TextChoices):
        PAYSTACK = 'paystack', 'Paystack test'
        CASH = 'cash', 'Cash'
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        CASH_RECORDED = 'cash_recorded', 'Cash collection reported'
    ride = models.OneToOneField('rides.Ride', related_name='payment', on_delete=models.PROTECT)
    method = models.CharField(max_length=12, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount_kobo = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default='NGN')
    reference = models.CharField(max_length=80, unique=True, null=True, blank=True)
    provider_id = models.CharField(max_length=40, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(amount_kobo__gt=0), name='movego_payment_amount_positive')]
