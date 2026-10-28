"""Forgotten password (e-mailed link) and password change for a signed-in user."""
import logging

from django.contrib.auth import update_session_auth_hash
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts.history import record_history
from common.csrf import enforce_csrf
from common.request import get_client_ip
from common.security_log import log_security_event
from users import lockout
from users.models import User
from users.password_reset import can_reset_password, daily_request_allowed, find_user_for_reset
from users.serializers import (
    PasswordChangeSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, validate_new_password,
)
from users.tasks import send_password_reset_email
from users.throttles import PasswordChangeThrottle, PasswordResetConfirmThrottle, PasswordResetRequestThrottle
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

INVALID_RESET_LINK_CODE = 'invalid_reset_link'  # the frontend shows its own text for it
INVALID_RESET_LINK_MESSAGE = 'This link is invalid or has expired. Please request a new one.'
RESET_REQUESTED_MESSAGE = 'If this address is registered, we have sent a link to reset the password.'
PASSWORD_CHANGED_MESSAGE = 'Your password was changed.'


def _queue_reset_email(user):
    """Hand the mail to the worker; a broken queue must not change the answer (it would reveal the account)."""
    try:
        send_password_reset_email.delay(user.id)
    except Exception:
        logger.exception('Could not queue the password reset e-mail for user %s', user.id)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRequestThrottle])
def request_password_reset(request):
    """
    Mail a password reset link to a registered address.

    The answer is the same for every address, so this cannot be used to find out who has an account.
    """
    enforce_csrf(request)
    serializer = PasswordResetRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(email=serializer.validated_data['email']).first()
    if user is not None and can_reset_password(user) and daily_request_allowed(user.email):
        _queue_reset_email(user)
        outcome = 'sent'
    else:
        outcome = 'ignored'
    log_security_event('password_reset_requested', request, user=user, level=logging.INFO, outcome=outcome)
    return Response({'detail': RESET_REQUESTED_MESSAGE})


def _password_rule_violation(user, password):
    """A 400 Response when the password breaks a password rule for this user, else None."""
    try:
        validate_new_password({'password': password, 'email': user.email, 'full_name': user.full_name},
                              privileged=user.is_staff or user.is_superuser)
    except DRFValidationError as error:
        return Response(error.detail, status=status.HTTP_400_BAD_REQUEST)
    return None


def _set_new_password(request, user, password, event):
    """Store the (already validated) password, clear lockouts, and write the event and history row."""
    user.set_password(password)
    user.save(update_fields=['password'])
    lockout.record_success(user, get_client_ip(request))
    log_security_event(event, request, user=user, level=logging.INFO)
    record_history(user, 'password_change', request)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetConfirmThrottle])
def confirm_password_reset(request):
    """
    Set a new password with the link from the reset e-mail.

    A broken, expired or used link gets one answer. The user is not signed in; every session they had ends.
    """
    enforce_csrf(request)
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = find_user_for_reset(serializer.validated_data['uid'], serializer.validated_data['token'])
    if user is None:
        log_security_event('password_reset_failed', request, reason='invalid_link')
        return Response({'error': INVALID_RESET_LINK_MESSAGE, 'code': INVALID_RESET_LINK_CODE},
                        status=status.HTTP_400_BAD_REQUEST)

    new_password = serializer.validated_data['password']
    violation = _password_rule_violation(user, new_password)
    if violation is not None:
        return violation

    _set_new_password(request, user, new_password, 'password_reset_completed')
    return Response({'detail': PASSWORD_CHANGED_MESSAGE})


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([PasswordChangeThrottle])
def change_password(request):
    """
    Change the password of the signed-in user. A wrong current password counts as a failed login.

    This session stays signed in; the account's other sessions end.
    """
    serializer = PasswordChangeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user, client_ip = request.user, get_client_ip(request)
    if lockout.is_locked(user, client_ip) or not user.check_password(serializer.validated_data['current_password']):
        lockout.record_failure(user, client_ip)
        log_security_event('password_change_failed', request, reason='wrong_current_password')
        return Response({'current_password': [_('The current password is incorrect.')]},
                        status=status.HTTP_400_BAD_REQUEST)
    new_password = serializer.validated_data['password']
    if new_password == serializer.validated_data['current_password']:
        return Response({'password': [_('The new password must be different from the current one.')]},
                        status=status.HTTP_400_BAD_REQUEST)
    violation = _password_rule_violation(user, new_password)
    if violation is not None:
        return violation

    _set_new_password(request, user, new_password, 'password_changed')
    update_session_auth_hash(request, user)
    return Response({'detail': PASSWORD_CHANGED_MESSAGE})
