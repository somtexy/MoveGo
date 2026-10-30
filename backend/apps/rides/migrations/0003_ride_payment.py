from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('rides','0002_ride_offer'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='RidePayment',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('method',models.CharField(choices=[('paystack','Paystack test'),('cash','Cash')],max_length=12)),
            ('status',models.CharField(choices=[('pending','Pending'),('paid','Paid'),('failed','Failed'),('cash_recorded','Cash collection reported')],default='pending',max_length=20)),
            ('amount_kobo',models.PositiveBigIntegerField()),
            ('currency',models.CharField(default='NGN',max_length=3)),
            ('reference',models.CharField(blank=True,max_length=80,null=True,unique=True)),
            ('provider_id',models.CharField(blank=True,max_length=40)),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('updated_at',models.DateTimeField(auto_now=True)),
            ('recorded_by',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='+',to=settings.AUTH_USER_MODEL)),
            ('ride',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,related_name='payment',to='rides.ride')),
        ],options={'constraints':[models.CheckConstraint(condition=models.Q(amount_kobo__gt=0),name='movego_payment_amount_positive')]})
    ]
