"""Storage form of the SMS login code."""
import hashlib
import hmac

from django.conf import settings


def hash_otp(code):
    """
    Keyed hash (HMAC-SHA256 with SECRET_KEY) of an OTP code, as stored in `User.otp_code`.

    Only 10^6 codes exist, so a plain hash would be reversed instantly; the key keeps a stolen
    database copy from revealing live codes.
    """
    return hmac.new(settings.SECRET_KEY.encode(), str(code).encode(), hashlib.sha256).hexdigest()
