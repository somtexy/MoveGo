from django.urls import path
from .fare_api import fare_quotes

urlpatterns = [
    path("quotes/", fare_quotes, name="fare-quotes"),
]
