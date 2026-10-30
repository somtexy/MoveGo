from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Ride",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pickup_label", models.CharField(max_length=255)),
                ("destination_label", models.CharField(max_length=255)),
                ("pickup_latitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("pickup_longitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("destination_latitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("destination_longitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("category", models.CharField(max_length=30)),
                ("status", models.CharField(choices=[("requested", "Requested"), ("searching", "Searching"), ("assigned", "Driver assigned"), ("arriving", "Driver arriving"), ("arrived", "Driver arrived"), ("started", "Trip started"), ("completed", "Completed"), ("cancelled", "Cancelled")], db_index=True, default="requested", max_length=12)),
                ("estimated_fare_kobo", models.PositiveBigIntegerField(blank=True, null=True)),
                ("final_fare_kobo", models.PositiveBigIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("passenger", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="passenger_rides", to=settings.AUTH_USER_MODEL)),
                ("driver", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="driver_rides", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at", "-id")},
        ),
        migrations.AddConstraint(model_name="ride", constraint=models.CheckConstraint(condition=models.Q(("driver__isnull", True), models.Q(("passenger", models.F("driver")), _negated=True), _connector="OR"), name="movego_driver_not_passenger")),
    ]
