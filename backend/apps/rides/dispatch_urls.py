from django.urls import path
from . import dispatch_api

urlpatterns = [
    path('rides/<int:ride_id>/offer/', dispatch_api.request_offer, name='dispatch-request-offer'),
    path('rides/<int:ride_id>/status/', dispatch_api.offer_status, name='dispatch-offer-status'),
    path('driver/offer/', dispatch_api.my_offer, name='dispatch-driver-offer'),
    path('driver/offers/<int:offer_id>/respond/', dispatch_api.respond, name='dispatch-driver-respond'),
]
