"""
Rate limits for the authentication endpoints.

Every limit here is keyed by something the caller cannot change freely: the client IP or the
logged-in account.
"""
import os
import sys

from common.throttling import BlockAnonRateThrottle

# Throttling is off while tests run; the tests that check a limit patch this flag back to False
TESTING = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST')


class IPRateThrottle(BlockAnonRateThrottle):
    """
    Throttle keyed by client IP for every caller.

    DRF's AnonRateThrottle skips logged-in users, so a throwaway account would
    lift the login and registration limits.
    """

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}

    def allow_request(self, request, view):
        # Disable throttling during tests
        if TESTING:
            return True
        return super().allow_request(request, view)


class LoginRateThrottle(IPRateThrottle):
    """Rate throttle for login endpoint - 10 requests per minute per IP."""
    rate = '10/min'
    scope = 'login'


class RegisterRateThrottle(IPRateThrottle):
    """Rate throttle for registration endpoint - 5 requests per minute per IP."""
    rate = '5/min'
    scope = 'register'


class PasswordResetRequestThrottle(IPRateThrottle):
    """Reset e-mails requested from one address: 5 per hour."""
    rate = '5/hour'
    scope = 'password_reset_request'


class PasswordResetConfirmThrottle(IPRateThrottle):
    """Reset links tried from one address: 10 per hour."""
    rate = '10/hour'
    scope = 'password_reset_confirm'


class AccountRateThrottle(IPRateThrottle):
    """Keyed by the logged-in account, not by anything the client puts in the request."""

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': f'user-{request.user.pk}'}


class PasswordChangeThrottle(AccountRateThrottle):
    """Password changes (and wrong current passwords) per account: 5 per minute."""
    rate = '5/min'
    scope = 'password_change'


class TwoFactorLoginThrottle(IPRateThrottle):
    """Codes tried from one network: 10 per minute (the lockout stops guessing sooner)."""
    rate = '10/min'
    scope = 'two_factor_login'


class TwoFactorSetupThrottle(AccountRateThrottle):
    """Setup and confirm calls per account: 10 per minute."""
    rate = '10/min'
    scope = 'two_factor_setup'
