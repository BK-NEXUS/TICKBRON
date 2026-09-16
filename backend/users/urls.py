"""
URL configuration for the users app.

This module contains URL patterns for user authentication and management endpoints.
"""
from django.urls import path
from users.views import register, login_view, logout_view, me, refresh_session

app_name = 'users'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('refresh/', refresh_session, name='refresh_session'),
    path('me/', me, name='me'),
]