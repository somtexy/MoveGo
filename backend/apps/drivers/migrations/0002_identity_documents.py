from django.db import migrations, models
import apps.drivers.models


class Migration(migrations.Migration):
    dependencies = [('drivers', '0001_initial')]
    operations = [
        migrations.AddField('driverprofile', 'first_name', models.CharField(max_length=60, blank=True)),
        migrations.AddField('driverprofile', 'last_name', models.CharField(max_length=60, blank=True)),
        migrations.AddField('driverprofile', 'nin', models.CharField(max_length=11, blank=True)),
        migrations.AddField('driverprofile', 'nin_document', models.FileField(upload_to='driver_docs/nin/', storage=apps.drivers.models.private_driver_storage, blank=True)),
        migrations.AddField('driverprofile', 'license_photo', models.FileField(upload_to='driver_docs/license/', storage=apps.drivers.models.private_driver_storage, blank=True)),
        migrations.AddField('driverprofile', 'selfie_photo', models.FileField(upload_to='driver_docs/selfie/', storage=apps.drivers.models.private_driver_storage, blank=True)),
    ]
