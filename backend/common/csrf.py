"""CSRF check for public endpoints that start a session."""
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.exceptions import PermissionDenied


class _CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # Return the reason instead of an HttpResponse, like DRF's own SessionAuthentication
        return reason


def enforce_csrf(request):
    """
    Raise 403 unless the request carries a valid CSRF token.

    DRF checks CSRF only for a request that already has a session user, so an anonymous login,
    registration or OTP call skipped it: a cross-site page could log the victim into the
    attacker's account (login CSRF). The SPA already sends X-CSRFToken on every unsafe call.
    """
    check = _CSRFCheck(lambda request: None)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise PermissionDenied(f'CSRF Failed: {reason}')
