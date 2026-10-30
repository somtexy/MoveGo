from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('accounts', '0003_google_identity'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='AppPIN', fields=[
        ('id', models.BigAutoField(primary_key=True, serialize=False)),
        ('encoded_pin', models.CharField(max_length=256)),
        ('failed_attempts', models.PositiveIntegerField(default=0)),
        ('locked_until', models.DateTimeField(blank=True, null=True)),
        ('updated_at', models.DateTimeField(auto_now=True)),
        ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='movego_app_pin', to=settings.AUTH_USER_MODEL)),
    ])]
