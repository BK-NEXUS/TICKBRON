"""
URL configuration for the users app.

This module contains URL patterns for user authentication and management endpoints.
"""
from django.urls import path
from users.views import register, login_view, logout_view, me, refresh_session, request_otp, verify_otp, update_profile, csrf_token, request_phone_verification, confirm_phone_verification

app_name = 'users'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('refresh/', refresh_session, name='refresh_session'),
    path('csrf/', csrf_token, name='csrf_token'),
    path('me/', me, name='me'),
    path('me/update/', update_profile, name='update_profile'),
    path('otp/request/', request_otp, name='request_otp'),
    path('otp/verify/', verify_otp, name='verify_otp'),
    path('phone/verify/request/', request_phone_verification, name='request_phone_verification'),
    path('phone/verify/confirm/', confirm_phone_verification, name='confirm_phone_verification'),
]