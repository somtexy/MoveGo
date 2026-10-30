from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [migrations.CreateModel(name="PhoneOTP", fields=[
        ("id", models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name="ID")),
        ("phone", models.CharField(max_length=16, unique=True)),
        ("code_digest", models.CharField(max_length=64, blank=True)),
        ("expires_at", models.DateTimeField(null=True, blank=True)),
        ("last_sent_at", models.DateTimeField(null=True, blank=True)),
        ("window_started_at", models.DateTimeField(null=True, blank=True)),
        ("sends_in_window", models.PositiveSmallIntegerField(default=0)),
        ("attempts", models.PositiveSmallIntegerField(default=0)),
        ("verified_at", models.DateTimeField(null=True, blank=True)),
    ])]
