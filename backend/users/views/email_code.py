"""The code steps of sign-up and sign-in: type the mailed code, or ask for a new one. Rules: users/email_codes.py."""
import logging

from django.contrib.auth import login
from django.db import IntegrityError
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accounts.history import record_history
from common.csrf import enforce_csrf
from common.request import get_client_ip, object_body
from common.security_log import log_security_event
from users import email_codes, lockout
from users.models import User
from users.serializers import UserSerializer
from users.sessions import start_session
from users.throttles import EmailCodeSendThrottle, EmailCodeVerifyThrottle
from users.views.auth import _login_failed_response, create_verified_user, mail_failed_response, too_soon_response

MAX_EMAIL_LENGTH = 254


def _address(value):
    """The address as the sign-up stored it (trimmed, lower case), or None when it is not text of a sensible size."""
    if not isinstance(value, str):
        return None
    value = value.strip().lower()
    return value if 0 < len(value) <= MAX_EMAIL_LENGTH else None


def _wrong_code_response():
    return Response({'detail': _('The code is wrong or has expired.')}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([EmailCodeVerifyThrottle])
def register_verify(request):
    """Last step of sign-up. Body: email, code. The right code makes the account, confirms the address and signs in."""
    enforce_csrf(request)
    body = object_body(request)
    email = _address(body.get('email'))
    waiting = email_codes.verify('register', email, body.get('code')) if email else None
    if not waiting:
        log_security_event('email_code_failed', request, reason='bad_code', purpose='register')
        return _wrong_code_response()
    try:
        user = create_verified_user(waiting)
    except IntegrityError:  # the address got an account while the code was waiting
        return Response({'email': [_('User with this email already exists.')]}, status=status.HTTP_400_BAD_REQUEST)
    login(request, user)
    log_security_event('account_created', request, user=user, level=logging.INFO)
    record_history(user, 'account_created', request)
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([EmailCodeSendThrottle])
def register_resend(request):
    """A new code for a sign-up that is waiting (after a minute; 5 mails an hour). Body: email."""
    enforce_csrf(request)
    email = _address(object_body(request).get('email'))
    if email is None or not email_codes.waiting('register', email):
        return Response({'detail': _('This sign-up has expired. Please start again.')}, status=status.HTTP_400_BAD_REQUEST)
    try:
        email_codes.issue('register', email, email, keep_payload_of=email)
    except email_codes.TooSoon as error:
        return too_soon_response(error)
    except email_codes.SendFailed:
        return mail_failed_response()
    except LookupError:
        return Response({'detail': _('This sign-up has expired. Please start again.')}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'email_code_required': True, 'email': email, 'expires_in': email_codes.LIFETIME_SECONDS,
                     'resend_after': email_codes.RESEND_AFTER_SECONDS})


def _pending_login_user(request):
    user_id = email_codes.pending_login_user_id(request)
    return User.objects.filter(pk=user_id, is_active=True).first() if user_id else None


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([EmailCodeVerifyThrottle])
def login_email_code(request):
    """Second step of the sign-in of a guest or hotel owner: the password was accepted, now the mailed code."""
    enforce_csrf(request)
    user, client_ip = _pending_login_user(request), get_client_ip(request)
    if user is None or lockout.is_locked(user, client_ip):
        log_security_event('email_code_failed', request, user=user, reason='no_password_step' if user is None else 'locked',
                           purpose='login')
        return _login_failed_response()

    if email_codes.verify('login', str(user.pk), object_body(request).get('code')) is None:
        lockout.record_failure(user, client_ip)
        log_security_event('email_code_failed', request, user=user, reason='bad_code', purpose='login')
        return _login_failed_response()

    email_codes.forget_login_step(request)
    if not user.email_verified:  # the code came to this mailbox: that proves the address
        user.email_verified = True
        user.save(update_fields=['email_verified'])
    start_session(request, user, client_ip, method='password+email_code')
    return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([EmailCodeSendThrottle])
def login_email_code_resend(request):
    """A new code for the sign-in that is waiting (after a minute; 5 mails an hour)."""
    enforce_csrf(request)
    user = _pending_login_user(request)
    if user is None:
        return _login_failed_response()
    try:
        email_codes.issue('login', str(user.pk), user.email)
    except email_codes.TooSoon as error:
        return too_soon_response(error)
    except email_codes.SendFailed:
        return mail_failed_response()
    email_codes.remember_login_step(request, user)
    return Response({'email_code_required': True, 'email_hint': email_codes.hint(user.email),
                     'expires_in': email_codes.LIFETIME_SECONDS, 'resend_after': email_codes.RESEND_AFTER_SECONDS})
