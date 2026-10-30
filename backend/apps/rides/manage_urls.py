from django.urls import path
from .manage_api import active_request, cancel_request

urlpatterns = [
    path('active/', active_request, name='movego-active-request'),
    path('<int:ride_id>/cancel/', cancel_request, name='movego-cancel-request'),
]
