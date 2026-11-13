"""Eki basqıshlı kirisiwi joq administratordı sazlaw ekranı ishinde ustap turadı."""
from django.http import JsonResponse
from django.utils.translation import gettext as _

from users.two_factor import needs_setup

# Eki basqıshlı kirisiwi joq session ele neni shaqıra aladı: men kimmen, shıǵıw, CSRF token, sazlawdıń ózi
ALLOWED_PREFIXES = (
    '/api/v1/auth/me/', '/api/v1/auth/logout/', '/api/v1/auth/csrf/', '/api/v1/auth/refresh/', '/api/v1/auth/2fa/',
)


class TwoFactorSetupMiddleware:
    """Kirgen administrator ekinshi basqıshtı sazlamaǵansha sazlaw shaqırıwlarınan basqa hár API shaqırıwına 403."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.path.startswith('/api/') and not request.path.startswith(ALLOWED_PREFIXES)
                and request.user.is_authenticated and needs_setup(request.user)):
            return JsonResponse(
                {'detail': _('Set up two-step sign-in first.'), 'code': 'two_factor_setup_required'}, status=403)
        return self.get_response(request)
