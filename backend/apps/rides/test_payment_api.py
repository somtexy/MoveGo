"""Offline Step 44 tests: no requests to Paystack network."""
import hashlib
import hmac
import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import Client,TestCase
from apps.accounts.models import RiderProfile
from .models import Ride
from .payment_models import RidePayment

class PaymentTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.passenger=User.objects.create_user(username='pay44p',email='p@example.org',password='Password123!')
        self.driver=User.objects.create_user(username='pay44d',password='Password123!')
        self.other=User.objects.create_user(username='pay44o',password='Password123!')
        for user,role,phone in [(self.passenger,RiderProfile.Role.PASSENGER,'+2348000440001'),(self.driver,RiderProfile.Role.DRIVER,'+2348000440002'),(self.other,RiderProfile.Role.PASSENGER,'+2348000440003')]:
            RiderProfile.objects.create(user=user,role=role,phone=phone,phone_verified=True)
        self.ride=Ride.objects.create(passenger=self.passenger,driver=self.driver,pickup_label='A',destination_label='B',category='Ride',status=Ride.Status.COMPLETED,estimated_fare_kobo=120000)
        self.init=f'/api/payments/{self.ride.pk}/initialize/'
    def post(self,path,data=None):return self.client.post(path,json.dumps(data if data is not None else {}),content_type='application/json')
    def test_login_and_ride_ownership(self):
        self.assertEqual(self.client.get(f'/api/payments/{self.ride.pk}/status/').status_code,401)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'/api/payments/{self.ride.pk}/status/').status_code,404)
        self.assertEqual(self.post(self.init).status_code,404)
    def test_cash_by_driver_only(self):
        url=f'/api/payments/{self.ride.pk}/cash/'
        self.client.force_login(self.passenger);self.assertEqual(self.post(url,{'confirm_collected':True}).status_code,404)
        self.client.force_login(self.driver);self.assertEqual(self.post(url,{'confirm_collected':True}).status_code,200)
        self.assertEqual(self.post(url,{'confirm_collected':True}).status_code,409)
        self.assertEqual(RidePayment.objects.get(ride=self.ride).status,'cash_recorded')
    def test_cash_requires_completed(self):
        Ride.objects.filter(pk=self.ride.pk).update(status=Ride.Status.STARTED)
        self.client.force_login(self.driver)
        self.assertEqual(self.post(f'/api/payments/{self.ride.pk}/cash/',{'confirm_collected':True}).status_code,404)
    @patch('apps.rides.payment_api.paystack_call')
    @patch('apps.rides.payment_api.secret',return_value='sk_test_fake')
    def test_initialize_server_amount(self,secret_mock,call):
        call.return_value={'reference':'wrong','authorization_url':'https://checkout.paystack.com/foo'}
        self.client.force_login(self.passenger)
        response=self.post(self.init,{'amount':1})
        self.assertEqual(response.status_code,400)
        def answer(method,path,body):return {'reference':body['reference'],'authorization_url':'https://checkout.paystack.com/fake'}
        call.side_effect=answer
        response=self.post(self.init,{})
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(call.call_args.args[2]['amount'],120000)
        self.assertEqual(self.post(self.init,{}).status_code,409)
    @patch('apps.rides.payment_api.paystack_call')
    @patch('apps.rides.payment_api.secret',return_value='sk_test_fake')
    def test_verify_amount_and_environment(self,secret_mock,call):
        payment=RidePayment.objects.create(ride=self.ride,method='paystack',amount_kobo=120000,reference='MGtestref')
        self.client.force_login(self.passenger)
        url=f'/api/payments/{self.ride.pk}/verify/'
        call.return_value={'status':'success','reference':'MGtestref','amount':1,'currency':'NGN','domain':'test'}
        self.assertEqual(self.post(url).status_code,409)
        call.return_value={'status':'success','reference':'MGtestref','amount':120000,'currency':'NGN','domain':'live'}
        self.assertEqual(self.post(url).status_code,409)
        call.return_value={'status':'success','reference':'MGtestref','amount':120000,'currency':'NGN','domain':'test','id':123}
        self.assertEqual(self.post(url).status_code,200)
        self.assertEqual(self.post(url).status_code,200)
        payment.refresh_from_db();self.assertEqual(payment.status,'paid')
    @patch('apps.rides.payment_api.paystack_call')
    @patch('apps.rides.payment_api.secret',return_value='sk_test_fake')
    def test_webhook_signature_and_verify(self,secret_mock,call):
        RidePayment.objects.create(ride=self.ride,method='paystack',amount_kobo=120000,reference='MGtestweb')
        body=json.dumps({'event':'charge.success','data':{'reference':'MGtestweb'}}).encode()
        url='/api/payments/webhook/'
        self.assertEqual(self.client.post(url,body,content_type='application/json').status_code,403)
        sig=hmac.new(b'sk_test_fake',body,hashlib.sha512).hexdigest()
        call.return_value={'reference':'MGtestweb','status':'success','amount':120000,'currency':'NGN','domain':'test'}
        self.assertEqual(self.client.post(url,body,content_type='application/json',HTTP_X_PAYSTACK_SIGNATURE=sig).status_code,200)
        self.assertEqual(RidePayment.objects.get(ride=self.ride).status,'paid')
    def test_csrf(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.driver)
        self.assertEqual(client.post(f'/api/payments/{self.ride.pk}/cash/',json.dumps({'confirm_collected':True}),content_type='application/json').status_code,403)
    def test_latest_private(self):
        self.client.force_login(self.passenger);self.assertEqual(self.client.get('/api/payments/latest/').json()['ride']['id'],self.ride.pk)
        self.client.force_login(self.other);self.assertIsNone(self.client.get('/api/payments/latest/').json()['ride'])
