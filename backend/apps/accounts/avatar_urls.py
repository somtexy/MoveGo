from django.urls import path
from .avatar_api import avatar_detail
urlpatterns = [path('auth/avatar/', avatar_detail, name='movego-avatar')]
