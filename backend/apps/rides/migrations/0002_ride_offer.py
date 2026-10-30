from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('rides', '0001_initial'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='RideOffer', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('expired', 'Expired'), ('cancelled', 'Cancelled')], db_index=True, default='pending', max_length=12)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('expires_at', models.DateTimeField(db_index=True)),
            ('responded_at', models.DateTimeField(blank=True, null=True)),
            ('driver', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='received_ride_offers', to=settings.AUTH_USER_MODEL)),
            ('ride', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dispatch_offers', to='rides.ride')),
        ]),
        migrations.AddConstraint(model_name='rideoffer', constraint=models.UniqueConstraint(condition=models.Q(status='pending'), fields=('ride',), name='movego_one_pending_offer_per_ride')),
        migrations.AddConstraint(model_name='rideoffer', constraint=models.UniqueConstraint(fields=('ride', 'driver'), name='movego_one_offer_per_driver_per_ride')),
    ]
