from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name="RiderProfile", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("role", models.CharField(choices=[("passenger", "Passenger"), ("driver", "Driver")], default="passenger", max_length=12)),
        ("phone", models.CharField(blank=True, max_length=20)),
        ("phone_verified", models.BooleanField(default=False)),
        ("created_at", models.DateTimeField(auto_now_add=True)),
        ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="movego_profile", to=settings.AUTH_USER_MODEL)),
    ])]
