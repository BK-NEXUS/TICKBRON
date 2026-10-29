"""Keeps an administrator without two-step sign-in inside the setup screen."""
from django.http import JsonResponse
from django.utils.translation import gettext as _

from users.two_factor import needs_setup

# What a session without two-step sign-in may still call: who am I, sign out, the CSRF token, the setup itself
ALLOWED_PREFIXES = (
    '/api/v1/auth/me/', '/api/v1/auth/logout/', '/api/v1/auth/csrf/', '/api/v1/auth/refresh/', '/api/v1/auth/2fa/',
)


class TwoFactorSetupMiddleware:
    """403 on every API call except the setup ones while the signed-in administrator has not set up the second step."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.path.startswith('/api/') and not request.path.startswith(ALLOWED_PREFIXES)
                and request.user.is_authenticated and needs_setup(request.user)):
            return JsonResponse(
                {'detail': _('Set up two-step sign-in first.'), 'code': 'two_factor_setup_required'}, status=403)
        return self.get_response(request)
