"""
Views for user authentication and management.

This module contains views for user registration, login, and session management.
"""
import logging
import sys
import os
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.middleware.csrf import get_token
from users.models import User
from users.password_reset import can_reset_password, daily_request_allowed, find_user_for_reset
from users.serializers import (
    ConfirmPhoneSerializer, PasswordChangeSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer,
    RequestOTPSerializer, UserLoginSerializer, UserRegistrationSerializer, UserSerializer, UserUpdateSerializer,
    VerifyOTPSerializer, validate_new_password,
)
from users.tasks import send_password_reset_email
from users import lockout
from users.validators import parse_phone_number
from users.services import OTPService
from common.csrf import enforce_csrf
from common.request import get_client_ip
from common.security_log import log_security_event
from accounts.history import record_history

logger = logging.getLogger(__name__)

# Check if running in test mode
TESTING = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST')

# One message for every failed login, so responses do not reveal whether an
# email exists or an account is locked
LOGIN_FAILED_MESSAGE = 'Invalid credentials. If you have made several failed attempts, please try again later.'


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

    def allow_request(self, request, view):
        # Disable throttling during tests
        if TESTING:
            return True
        return super().allow_request(request, view)


class RegisterRateThrottle(IPRateThrottle):
    """Rate throttle for registration endpoint - 5 requests per minute per IP."""
    rate = '5/min'
    scope = 'register'

    def allow_request(self, request, view):
        # Disable throttling during tests
        if TESTING:
            return True
        return super().allow_request(request, view)


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

    def allow_request(self, request, view):
        # Disable throttling during tests
        if TESTING:
            return True
        return super().allow_request(request, view)


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
        return self.cache_format % {'scope': self.scope, 'ident': request.user.phone_number or f'user-{request.user.pk}'}


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


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def register(request):
    """
    Register a new user.
    
    Creates a new user account with email and password.
    Uses session-based authentication with secure cookies.
    """
    enforce_csrf(request)
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Auto-login after registration
        login(request, user)
        log_security_event('account_created', request, user=user, level=logging.INFO)
        record_history(user, 'account_created', request)
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    """
    Login user with email and password.
    
    Authenticates user and creates a session using secure cookies.
    Includes lockout protection after failed attempts (see users.lockout).
    
    Unknown email, wrong password, inactive and locked accounts all get the
    same 401 response, so the endpoint does not reveal which emails exist.
    """
    enforce_csrf(request)
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
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
        
        lockout.record_success(authenticated_user, client_ip)
        authenticated_user.last_login_ip = client_ip
        authenticated_user.save(update_fields=['last_login_ip'])
        
        login(request, authenticated_user)
        log_security_event('login_success', request, user=authenticated_user, level=logging.INFO, method_used='password')
        record_history(authenticated_user, 'login', request)
        return Response(
            UserSerializer(authenticated_user).data,
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def _login_failed_response():
    return Response({'detail': LOGIN_FAILED_MESSAGE}, status=status.HTTP_401_UNAUTHORIZED)



@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """
    Logout user and destroy session.
    
    Clears the session cookie and logs out the user.
    """
    account = request.user if request.user.is_authenticated else None
    if account is not None:
        log_security_event('logout', request, user=account, level=logging.INFO)
        record_history(account, 'logout', request)
    logout(request)
    return Response(
        {'detail': 'Successfully logged out.'},
        status=status.HTTP_200_OK
    )


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


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def me(request):
    """
    Get current user information.
    
    Returns the profile of the currently authenticated user.
    """
    if request.user.is_authenticated:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    return Response(
        {'detail': 'Authentication credentials were not provided.'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update current user profile.
    
    Allows authenticated users to update their profile information including
    contact preferences (whatsapp, telegram, preferred_contact_method).
    """
    serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_session(request):
    """
    Refresh user session.
    
    Validates and refreshes the current session.
    """
    if request.user.is_authenticated:
        return Response(
            UserSerializer(request.user).data,
            status=status.HTTP_200_OK
        )
    return Response(
        {'detail': 'No active session found.'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPRequestRateThrottle, OTPRequestIPThrottle, OTPDailyNumberThrottle])
def request_otp(request):
    """
    Request OTP code for phone-based authentication.
    
    Generates and sends an OTP code to the provided phone number.
    In test mode, the OTP code is returned in the response.
    Rate-limited to 3 requests per minute per phone number.
    Registered, unknown and locked numbers get the same 200 response.
    """
    enforce_csrf(request)
    serializer = RequestOTPSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']

        otp_service = OTPService()
        result = otp_service.send_otp(phone_number, client_ip=get_client_ip(request))

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPVerifyRateThrottle])
def verify_otp(request):
    """
    Verify OTP code and establish session.
    
    Verifies the OTP code for the provided phone number.
    On successful verification, establishes a session using the same
    mechanism as password login.
    Rate-limited to 5 attempts per minute per phone number; locked accounts
    get the same 400 as a wrong code, without the code being checked.
    """
    enforce_csrf(request)
    serializer = VerifyOTPSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']
        
        client_ip = get_client_ip(request)
        otp_service = OTPService()
        result = otp_service.verify_otp(phone_number, otp_code, client_ip=client_ip)

        if result['success']:
            try:
                user = User.objects.get(id=result['user_id'])

                # Clear failure counters on successful login
                lockout.record_success(user, client_ip)

                # Store login IP
                user.last_login_ip = client_ip
                user.save(update_fields=['last_login_ip'])
                
                # Establish session using the same mechanism as password login
                login(request, user)
                log_security_event('login_success', request, user=user, level=logging.INFO, method_used='otp')
                record_history(user, 'login', request)

                return Response(
                    UserSerializer(user).data,
                    status=status.HTTP_200_OK
                )
            except User.DoesNotExist:
                return Response(
                    {'detail': 'User not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        # Lock checks and failure counting happen inside OTPService.verify_otp;
        # unknown numbers, wrong codes and locked accounts look the same here
        log_security_event('otp_login_failed', request)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([PhoneVerifyRequestThrottle, PhoneVerifyDailyThrottle, OwnNumberDailyThrottle])
def request_phone_verification(request):
    """
    Send a code to the logged-in user's own phone number.

    The number is taken from the account; anything the client sends is ignored.
    """
    user = request.user
    if not user.phone_number:
        return Response({'error': 'Add a phone number first.', 'code': 'phone_missing'},
                        status=status.HTTP_400_BAD_REQUEST)
    if user.phone_verified:
        return Response({'error': 'This phone number is already verified.', 'code': 'phone_already_verified'},
                        status=status.HTTP_400_BAD_REQUEST)
    result = OTPService().send_phone_verification(user, client_ip=get_client_ip(request))
    return Response(result, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([PhoneVerifyConfirmThrottle])
def confirm_phone_verification(request):
    """Check the code sent to the user's number; success marks the number verified."""
    serializer = ConfirmPhoneSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    result = OTPService().confirm_phone_verification(
        request.user, serializer.validated_data['otp_code'], client_ip=get_client_ip(request)
    )
    if not result['success']:
        return Response({'error': result['message'], 'code': 'otp_invalid'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(UserSerializer(result['user']).data, status=status.HTTP_200_OK)


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
        validate_new_password({'password': password, 'email': user.email, 'full_name': user.full_name})
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
        return Response({'current_password': ['The current password is incorrect.']},
                        status=status.HTTP_400_BAD_REQUEST)
    new_password = serializer.validated_data['password']
    if new_password == serializer.validated_data['current_password']:
        return Response({'password': ['The new password must be different from the current one.']},
                        status=status.HTTP_400_BAD_REQUEST)
    violation = _password_rule_violation(user, new_password)
    if violation is not None:
        return violation

    _set_new_password(request, user, new_password, 'password_changed')
    update_session_auth_hash(request, user)
    return Response({'detail': PASSWORD_CHANGED_MESSAGE})
