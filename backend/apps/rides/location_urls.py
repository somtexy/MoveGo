from django.urls import path
from .location_api import location_suggestions, driving_route, reverse_location

urlpatterns = [
    path('autocomplete/', location_suggestions, name='location-autocomplete'),
    path('route/', driving_route, name='location-route'),
    path('reverse/', reverse_location, name='location-reverse'),
]
