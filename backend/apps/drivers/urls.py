from django.urls import path
from . import api, location_api

urlpatterns = [
    path('location/', location_api.update_location, name='driver-location-update'),
    path('location/status/', location_api.location_status, name='driver-location-status'),
    path('location/stop/', location_api.stop_location, name='driver-location-stop'),
    path('me/', api.me, name='driver-me'),
    path('register/', api.register, name='driver-register'),
    path('review-document/<int:profile_id>/<str:kind>/', api.review_document, name='driver-review-document'),
    path('availability/', api.availability, name='driver-availability'),
]
