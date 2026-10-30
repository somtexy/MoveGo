from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='DriverProfile', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('full_name', models.CharField(max_length=120)),
            ('license_number', models.CharField(max_length=64)),
            ('vehicle_make', models.CharField(max_length=60)),
            ('vehicle_model', models.CharField(max_length=60)),
            ('vehicle_color', models.CharField(max_length=40)),
            ('plate_number', models.CharField(max_length=24)),
            ('review_status', models.CharField(choices=[('pending', 'Pending review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=12)),
            ('is_online', models.BooleanField(default=False)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='driver_profile', to=settings.AUTH_USER_MODEL)),
        ]),
    ]
