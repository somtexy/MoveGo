from django.urls import path
from .views import passenger_ride_history

urlpatterns = [
    path("history/", passenger_ride_history, name="passenger-ride-history"),
]
