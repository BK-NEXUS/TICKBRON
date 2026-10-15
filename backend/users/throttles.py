"""
Rate limits for the authentication endpoints.

Every limit here is keyed by something the caller cannot change freely: the client IP, the
normalized phone number, or the logged-in account.
"""
import os
import sys

from rest_framework.throttling import AnonRateThrottle

from users.validators import parse_phone_number

# Throttling is off while tests run; the tests that check a limit patch this flag back to False
TESTING = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST')


class IPRateThrottle(AnonRateThrottle):
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


class PhoneNumberRateThrottle(IPRateThrottle):
    """
    Base throttle keyed by the phone number in the request body.

    The number is normalized the same way the serializers normalize it, so
    another spelling of it ("+998 90 ...", extra whitespace) does not produce a
    fresh throttle bucket.
    """

    def get_cache_key(self, request, view):
        phone_number = ''
        if hasattr(request.data, 'get'):
            raw = str(request.data.get('phone_number') or '').strip()
            phone_number = parse_phone_number(raw) or raw
        if phone_number:
            return self.cache_format % {'scope': self.scope, 'ident': phone_number}
        return super().get_cache_key(request, view)


class OTPRequestRateThrottle(PhoneNumberRateThrottle):
    """Rate throttle for OTP request endpoint - 3 requests per minute per phone number."""
    rate = '3/min'
    scope = 'otp_request'


class PasswordResetRequestThrottle(IPRateThrottle):
    """Reset e-mails requested from one address: 5 per hour."""
    rate = '5/hour'
    scope = 'password_reset_request'


class PasswordResetConfirmThrottle(IPRateThrottle):
    """Reset links tried from one address: 10 per hour."""
    rate = '10/hour'
    scope = 'password_reset_confirm'


class OTPVerifyRateThrottle(PhoneNumberRateThrottle):
    """Rate throttle for OTP verify endpoint - 5 attempts per minute per phone number."""
    rate = '5/min'
    scope = 'otp_verify'


class OTPRequestIPThrottle(IPRateThrottle):
    """
    SMS budget per IP for the login code request, on top of the per-number limit.

    The per-number limit alone is bypassed by asking for a code for a new number every time.
    """
    rate = '60/hour'
    scope = 'otp_request_ip'


class OTPDailyNumberThrottle(PhoneNumberRateThrottle):
    """Codes sent to one number per day, whoever asks (login code and phone verification share it)."""
    rate = '10/day'
    scope = 'otp_request_day'


class OwnNumberDailyThrottle(OTPDailyNumberThrottle):
    """Same budget for the logged-in verification endpoints, which ignore the body: the account's own number."""

    def get_cache_key(self, request, view):
        ident = request.user.phone_number or f'user-{request.user.pk}'
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class AccountRateThrottle(IPRateThrottle):
    """Keyed by the logged-in account, not by anything the client puts in the request."""

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': f'user-{request.user.pk}'}


class PhoneVerifyRequestThrottle(AccountRateThrottle):
    rate = '3/min'
    scope = 'phone_verify_request'


class PhoneVerifyDailyThrottle(AccountRateThrottle):
    """An account can change its number and ask again, so the number's own budget is not enough."""
    rate = '20/day'
    scope = 'phone_verify_day'


class PhoneVerifyConfirmThrottle(AccountRateThrottle):
    rate = '5/min'
    scope = 'phone_verify_confirm'


class PasswordChangeThrottle(AccountRateThrottle):
    """Password changes (and wrong current passwords) per account: 5 per minute."""
    rate = '5/min'
    scope = 'password_change'
