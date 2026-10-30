from django.urls import path
from .request_api import create_ride_request

urlpatterns = [
    path("", create_ride_request, name="create-ride-request"),
]
