"""
Views for user authentication and account management.

auth: sign-up, login, logout, CSRF token. profile: the user's own account.
otp: SMS login and phone verification. password: reset by e-mail link and change.
"""
from users.views.auth import csrf_token, login_view, logout_view, register
from users.views.otp import confirm_phone_verification, request_otp, request_phone_verification, verify_otp
from users.views.password import change_password, confirm_password_reset, request_password_reset
from users.views.profile import me, refresh_session, update_profile

__all__ = [
    'change_password', 'confirm_password_reset', 'confirm_phone_verification', 'csrf_token', 'login_view',
    'logout_view', 'me', 'refresh_session', 'register', 'request_otp', 'request_password_reset',
    'request_phone_verification', 'update_profile', 'verify_otp',
]
