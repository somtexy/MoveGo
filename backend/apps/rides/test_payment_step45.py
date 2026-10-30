"""Step 45 payment reliability regression tests; Paystack network is always mocked."""
import hashlib
import hmac
import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.accounts.models import RiderProfile
from .models import Ride
from .payment_models import RidePayment

class PaymentReliabilityTests(TestCase):
    def setUp(self):
        U=get_user_model()
        self.passenger=U.objects.create_user(username='rel45p',email='r45@example.test',password='Password123!')
        self.driver=U.objects.create_user(username='rel45d',password='Password123!')
        for user,role,phone in ((self.passenger,RiderProfile.Role.PASSENGER,'+2348000450001'),(self.driver,RiderProfile.Role.DRIVER,'+2348000450002')):
            RiderProfile.objects.create(user=user,role=role,phone=phone,phone_verified=True)
        self.ride=Ride.objects.create(passenger=self.passenger,driver=self.driver,pickup_label='A',destination_label='B',category='Ride',status=Ride.Status.COMPLETED,estimated_fare_kobo=120000)
        self.client.force_login(self.passenger)
    def post(self, path, obj=None):
        return self.client.post(path,json.dumps({} if obj is None else obj),content_type='application/json')
    @patch('apps.rides.payment_api.paystack_call')
    def test_verification_pending_never_marks_paid(self, provider):
        payment=RidePayment.objects.create(ride=self.ride,method='paystack',amount_kobo=120000,reference='MGpending45')
        provider.return_value={'reference':payment.reference,'status':'pending','amount':120000,'currency':'NGN','domain':'test'}
        self.assertEqual(self.post(f'/api/payments/{self.ride.pk}/verify/').status_code,409)
        payment.refresh_from_db();self.assertEqual(payment.status,'pending')
    @patch('apps.rides.payment_api.paystack_call')
    def test_paid_cannot_be_paid_again_as_cash(self,provider):
        payment=RidePayment.objects.create(ride=self.ride,method='paystack',amount_kobo=120000,reference='MGpaid45')
        provider.return_value={'reference':payment.reference,'status':'success','amount':120000,'currency':'NGN','domain':'test'}
        self.assertEqual(self.post(f'/api/payments/{self.ride.pk}/verify/').status_code,200)
        self.client.force_login(self.driver)
        self.assertEqual(self.post(f'/api/payments/{self.ride.pk}/cash/',{'confirm_collected':True}).status_code,409)
    @patch('apps.rides.payment_api.paystack_call')
    @patch('apps.rides.payment_api.secret',return_value='sk_test_fake')
    def test_duplicate_valid_webhooks_are_idempotent(self,secret_mock,provider):
        payment=RidePayment.objects.create(ride=self.ride,method='paystack',amount_kobo=120000,reference='MGwebhook45')
        body=json.dumps({'event':'charge.success','data':{'reference':payment.reference}}).encode()
        sig=hmac.new(b'sk_test_fake',body,hashlib.sha512).hexdigest()
        provider.return_value={'reference':payment.reference,'status':'success','amount':120000,'currency':'NGN','domain':'test'}
        for i in range(2):
            r=self.client.post('/api/payments/webhook/',body,content_type='application/json',HTTP_X_PAYSTACK_SIGNATURE=sig)
            self.assertEqual(r.status_code,200)
        payment.refresh_from_db();self.assertEqual(payment.status,'paid')
        self.assertEqual(RidePayment.objects.filter(ride=self.ride).count(),1)
    @patch('apps.rides.payment_api.paystack_call')
    @patch('apps.rides.payment_api.secret',return_value='sk_test_fake')
    def test_checkout_failure_remains_reconcilable(self,secret_mock,provider):
        provider.side_effect=TimeoutError('simulated upstream timeout')
        self.assertEqual(self.post(f'/api/payments/{self.ride.pk}/initialize/').status_code,502)
        payment=RidePayment.objects.get(ride=self.ride)
        self.assertEqual(payment.status,'pending')
        self.assertEqual(self.post(f'/api/payments/{self.ride.pk}/initialize/').status_code,409)
        self.assertEqual(payment.amount_kobo,120000)
