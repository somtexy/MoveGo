from . import pin_recovery
from django.urls import path
from . import pin_api
urlpatterns = [
    path('recovery/request/', pin_recovery.request_code),
    path('recovery/confirm/', pin_recovery.confirm_code),
    path('recovery/reset/', pin_recovery.reset_pin),
    path('status/',pin_api.status),
    path('setup/',pin_api.setup),
    path('verify/',pin_api.verify),
    path('change/',pin_api.change),
    path('recover/',pin_api.recover),
]
