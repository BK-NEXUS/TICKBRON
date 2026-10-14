"""
URL configuration for the users app.

This module contains URL patterns for user authentication and management endpoints.
"""
from django.urls import path
from users.views import (
    change_password, confirm_password_reset, confirm_phone_verification, csrf_token, login_view, logout_view, me,
    refresh_session, register, request_otp, request_password_reset, request_phone_verification, update_profile,
    verify_otp,
)

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
    path('password-reset/request/', request_password_reset, name='request_password_reset'),
    path('password-reset/confirm/', confirm_password_reset, name='confirm_password_reset'),
    path('password/change/', change_password, name='change_password'),
    path('phone/verify/request/', request_phone_verification, name='request_phone_verification'),
    path('phone/verify/confirm/', confirm_phone_verification, name='confirm_phone_verification'),
]