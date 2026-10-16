"""
Views for user authentication and account management.

auth: sign-up, login, logout, CSRF token. profile: the user's own account.
password: reset by e-mail link and change.
"""
from users.views.auth import csrf_token, login_view, logout_view, register
from users.views.password import change_password, confirm_password_reset, request_password_reset
from users.views.profile import me, refresh_session, update_profile

__all__ = [
    'change_password', 'confirm_password_reset', 'csrf_token', 'login_view', 'logout_view', 'me',
    'refresh_session', 'register', 'request_password_reset', 'update_profile',
]
