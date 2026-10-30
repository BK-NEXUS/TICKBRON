"""
URL configuration for the users app.

This module contains URL patterns for user authentication and management endpoints.
"""
from django.urls import path
from users.views import (
    change_password, confirm_password_reset, csrf_token, login_view, logout_view, me, refresh_session, register,
    request_password_reset, update_profile,
)
from users.views.two_factor import confirm_two_factor, login_two_factor, setup_two_factor

app_name = 'users'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('login/2fa/', login_two_factor, name='login_two_factor'),
    path('2fa/setup/', setup_two_factor, name='setup_two_factor'),
    path('2fa/confirm/', confirm_two_factor, name='confirm_two_factor'),
    path('logout/', logout_view, name='logout'),
    path('refresh/', refresh_session, name='refresh_session'),
    path('csrf/', csrf_token, name='csrf_token'),
    path('me/', me, name='me'),
    path('me/update/', update_profile, name='update_profile'),
    path('password-reset/request/', request_password_reset, name='request_password_reset'),
    path('password-reset/confirm/', confirm_password_reset, name='confirm_password_reset'),
    path('password/change/', change_password, name='change_password'),
]
