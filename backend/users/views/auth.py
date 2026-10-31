"""Sign-up, password login, logout and the CSRF token."""
import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.middleware.csrf import get_token
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accounts.history import record_history
from common.csrf import enforce_csrf
from common.request import get_client_ip
from common.security_log import log_security_event
from django.conf import settings
from django.db import IntegrityError, transaction

from users import email_codes, lockout, two_factor
from users.models import User
from users.serializers import UserLoginSerializer, UserRegistrationSerializer, UserSerializer
from users.sessions import start_session
from users.throttles import LoginRateThrottle, RegisterRateThrottle
from django.utils.translation import gettext as _

# One message for every failed login, so responses do not reveal whether an
# email exists or an account is locked
LOGIN_FAILED_MESSAGE = 'Invalid credentials. If you have made several failed attempts, please try again later.'


def _login_failed_response():
    return Response({'detail': LOGIN_FAILED_MESSAGE}, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def register(request):
    """
    Sign up with e-mail, name and password. With EMAIL_VERIFICATION_REQUIRED (the normal setting) nothing is created yet:
    a six-digit code goes to the address and the account is made by POST /auth/register/verify/. Without it the account
    is made at once and the new user is signed in.
    """
    enforce_csrf(request)
    serializer = UserRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if settings.EMAIL_VERIFICATION_REQUIRED:
        return _start_verified_sign_up(request, serializer.validated_data)

    user = serializer.save()
    login(request, user)
    log_security_event('account_created', request, user=user, level=logging.INFO)
    record_history(user, 'account_created', request)
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


def mail_failed_response():
    return Response({'detail': _('We could not send the code. Please try again in a moment.')},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE)


def too_soon_response(error):
    return Response({'detail': _('Please wait before asking for another code.'), 'retry_after': error.retry_after},
                    status=status.HTTP_429_TOO_MANY_REQUESTS, headers={'Retry-After': str(error.retry_after)})


def _start_verified_sign_up(request, data):
    """Keep the typed data (the password only as a hash) with a new code and mail the code; make no account yet."""
    email = data['email']
    waiting = {key: value for key, value in data.items() if key not in ('password', 'password_confirm')}
    waiting['password_hash'] = make_password(data['password'])
    try:
        email_codes.issue('register', email, email, payload=waiting)
    except email_codes.TooSoon as error:
        return too_soon_response(error)
    except email_codes.SendFailed:
        log_security_event('email_code_failed', request, reason='mail_not_sent', purpose='register')
        return mail_failed_response()
    log_security_event('email_code_sent', request, level=logging.INFO, purpose='register')
    return Response({'email_code_required': True, 'email': email, 'expires_in': email_codes.LIFETIME_SECONDS,
                     'resend_after': email_codes.RESEND_AFTER_SECONDS}, status=status.HTTP_202_ACCEPTED)


def create_verified_user(waiting):
    """The account of a confirmed sign-up: the stored password hash is used as it is, the address counts as confirmed."""
    fields = {key: value for key, value in waiting.items() if key != 'password_hash'}
    with transaction.atomic():
        user = User.objects.create_user(password=None, **fields)
        user.password = waiting['password_hash']
        user.email_verified = True
        user.save(update_fields=['password', 'email_verified'])
    return user


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    """
    Sign in with e-mail and password (lockout rules: see users.lockout).

    Unknown email, wrong password, inactive and locked accounts all get the
    same 401 response, so the endpoint does not reveal which emails exist.
    """
    enforce_csrf(request)
    serializer = UserLoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    client_ip = get_client_ip(request)

    user = User.objects.filter(email=email).first()
    if user is None or lockout.is_locked(user, client_ip):
        # Hash anyway so the response time does not reveal which case this is
        make_password(password)
        # The client sees one answer; the log says which case it was
        log_security_event('login_failed', request, user=user, reason='unknown_account' if user is None else 'locked')
        return _login_failed_response()

    authenticated_user = authenticate(request, username=email, password=password)
    if authenticated_user is None or not authenticated_user.is_active:
        lockout.record_failure(user, client_ip)
        log_security_event('login_failed', request, user=user, reason='bad_credentials')
        return _login_failed_response()

    if authenticated_user.two_factor_enabled:
        # Not signed in yet: the failure counters stay until the code is right too
        two_factor.remember_password_step(request, authenticated_user)
        return Response({'two_factor_required': True}, status=status.HTTP_200_OK)

    if email_codes.needs_code_at_login(authenticated_user):
        return _ask_for_login_code(request, authenticated_user)

    start_session(request, authenticated_user, client_ip, method='password')
    return Response(UserSerializer(authenticated_user).data, status=status.HTTP_200_OK)


def _ask_for_login_code(request, user):
    """The password is right: mail a code and wait for it; the session starts only when the code is typed."""
    ident = str(user.pk)
    try:
        email_codes.issue('login', ident, user.email)
    except email_codes.TooSoon as error:
        if error.retry_after > email_codes.RESEND_AFTER_SECONDS:  # the hourly limit, not "the last code is still fresh"
            return too_soon_response(error)
    except email_codes.SendFailed:
        log_security_event('email_code_failed', request, user=user, reason='mail_not_sent', purpose='login')
        return mail_failed_response()
    else:
        log_security_event('email_code_sent', request, user=user, level=logging.INFO, purpose='login')
    email_codes.remember_login_step(request, user)
    return Response({'email_code_required': True, 'email_hint': email_codes.hint(user.email),
                     'expires_in': email_codes.LIFETIME_SECONDS, 'resend_after': email_codes.RESEND_AFTER_SECONDS},
                    status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """End the session and clear its cookie."""
    account = request.user if request.user.is_authenticated else None
    if account is not None:
        log_security_event('logout', request, user=account, level=logging.INFO)
        record_history(account, 'logout', request)
    logout(request)
    return Response({'detail': _('Successfully logged out.')}, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_token(request):
    """
    Return a CSRF token for the X-CSRFToken header.

    The csrftoken cookie is HttpOnly, so the SPA cannot read it and asks here
    instead. get_token() also sets the cookie if the browser has none yet.
    Django rotates the token on login, so clients fetch a new one after it.
    """
    return Response({
        'csrf_token': get_token(request),
        # Lets the SPA skip /auth/me/ (a 401) when nobody is logged in
        'authenticated': request.user.is_authenticated,
    }, status=status.HTTP_200_OK)
