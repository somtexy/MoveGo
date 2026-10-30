from django.urls import path
from . import payment_api
urlpatterns=[
 path('latest/',payment_api.latest),
 path('<int:ride_id>/initialize/',payment_api.initialize),
 path('<int:ride_id>/verify/',payment_api.verify),
 path('<int:ride_id>/cash/',payment_api.cash),
 path('<int:ride_id>/status/',payment_api.status),
 path('webhook/',payment_api.webhook),
]
