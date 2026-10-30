from django.urls import path
from . import trip_api
urlpatterns = [
    path('my/',trip_api.my_trip,name='movego-trip-my'),
    path('<int:ride_id>/',trip_api.trip_status,name='movego-trip-status'),
    path('<int:ride_id>/advance/',trip_api.advance_trip,name='movego-trip-advance'),
]
