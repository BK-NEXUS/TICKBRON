"""Two-step sign-in: the code step of the login, and the setup screen's two calls."""
import logging

from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import (api_view, permission_classes,
                                       throttle_classes)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.csrf import enforce_csrf
from common.request import get_client_ip
from common.security_log import log_security_event
from users import lockout, two_factor
from users.serializers import UserSerializer
from users.sessions import start_session
from users.throttles import TwoFactorLoginThrottle, TwoFactorSetupThrottle
from users.views.auth import _login_failed_response


def _code_is_right(user, data):
    """Check the app's code, or else a backup code; returns the method name that worked, or None."""
    code, backup_code = data.get('code'), data.get('backup_code')
    if isinstance(code, str) and code and two_factor.accept_code(user, code):
        return 'totp'
    if isinstance(backup_code, str) and backup_code and two_factor.use_backup_code(user, backup_code):
        return 'backup_code'
    return None


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([TwoFactorLoginThrottle])
def login_two_factor(request):
    """Second step of the login: the password was accepted in the last 5 minutes, now the code (or a backup code)."""
    enforce_csrf(request)
    user, client_ip = two_factor.pending_user(request), get_client_ip(request)
    if user is None or lockout.is_locked(user, client_ip):
        log_security_event('two_factor_failed', request, user=user, reason='no_password_step' if user is None else 'locked')
        return _login_failed_response()

    method = _code_is_right(user, request.data)
    if method is None:
        lockout.record_failure(user, client_ip)
        log_security_event('two_factor_failed', request, user=user, reason='bad_code')
        return _login_failed_response()

    two_factor.forget_password_step(request)
    start_session(request, user, client_ip, method=f'password+{method}')
    return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([TwoFactorSetupThrottle])
def setup_two_factor(request):
    """Make a new secret for the signed-in user's authenticator app. Nothing is switched on until confirm."""
    if request.user.two_factor_enabled:
        return Response({'detail': _('Two-step sign-in is already on.')}, status=status.HTTP_400_BAD_REQUEST)
    secret = two_factor.new_secret()
    request.session[two_factor.SETUP_KEY] = secret
    return Response({'otpauth_uri': two_factor.provisioning_uri(secret, request.user.email), 'secret': secret})


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([TwoFactorSetupThrottle])
def confirm_two_factor(request):
    """The first right code from the app switches two-step sign-in on and returns the backup codes (once)."""
    secret = request.session.get(two_factor.SETUP_KEY)
    code = request.data.get('code')
    step = two_factor.matching_step(secret, code) if secret and isinstance(code, str) else None
    if step is None:
        return Response(
            {'detail': _('The code is not right. Check the time on your phone and try again.')},
            status=status.HTTP_400_BAD_REQUEST,
        )
    backup_codes = two_factor.enable(request.user, secret, step)
    request.session.pop(two_factor.SETUP_KEY, None)
    request.session.cycle_key()
    two_factor.end_other_sessions(request.user, request.session.session_key)
    log_security_event('two_factor_enabled', request, level=logging.INFO)
    return Response({'backup_codes': backup_codes})
