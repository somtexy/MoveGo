from django.urls import path
from .discovery_api import nearby_drivers
urlpatterns=[path('nearby/',nearby_drivers,name='nearby-drivers')]
