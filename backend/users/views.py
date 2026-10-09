"""
Views for user authentication and management.

This module contains views for user registration, login, and session management.
"""
import sys
import os
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.middleware.csrf import get_token
from users.models import User
from users.serializers import UserSerializer, UserRegistrationSerializer, UserLoginSerializer, RequestOTPSerializer, VerifyOTPSerializer, UserUpdateSerializer
from users import lockout
from users.validators import parse_phone_number
from users.services import OTPService
from common.request import get_client_ip

# Check if running in test mode
TESTING = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST')

# One message for every failed login, so responses do not reveal whether an
# email exists or an account is locked
LOGIN_FAILED_MESSAGE = 'Invalid credentials. If you have made several failed attempts, please try again later.'


class LoginRateThrottle(AnonRateThrottle):
    """Rate throttle for login endpoint - 10 requests per minute per IP."""
    rate = '10/min'
    scope = 'login'

    def allow_request(self, request, view):
        # Disable throttling during tests
        if TESTING:
            return True
        return super().allow_request(request, view)


class RegisterRateThrottle(AnonRateThrottle):
    """Rate throttle for registration endpoint - 5 requests per minute per IP."""
    rate = '5/min'
    scope = 'register'

    def allow_request(self, request, view):
        # Disable throttling during tests
        if TESTING:
            return True
        return super().allow_request(request, view)


class PhoneNumberRateThrottle(AnonRateThrottle):
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


class OTPVerifyRateThrottle(PhoneNumberRateThrottle):
    """Rate throttle for OTP verify endpoint - 5 attempts per minute per phone number."""
    rate = '5/min'
    scope = 'otp_verify'


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
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Auto-login after registration
        login(request, user)
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
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        client_ip = get_client_ip(request)
        
        user = User.objects.filter(email__iexact=email).first()
        if user is None or lockout.is_locked(user, client_ip):
            # Hash anyway so the response time does not reveal which case this is
            make_password(password)
            return _login_failed_response()
        
        authenticated_user = authenticate(request, username=user.email, password=password)
        if authenticated_user is None or not authenticated_user.is_active:
            lockout.record_failure(user, client_ip)
            return _login_failed_response()
        
        lockout.record_success(authenticated_user, client_ip)
        authenticated_user.last_login_ip = client_ip
        authenticated_user.save(update_fields=['last_login_ip'])
        
        login(request, authenticated_user)
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
@throttle_classes([OTPRequestRateThrottle])
def request_otp(request):
    """
    Request OTP code for phone-based authentication.
    
    Generates and sends an OTP code to the provided phone number.
    In test mode, the OTP code is returned in the response.
    Rate-limited to 3 requests per minute per phone number.
    Registered, unknown and locked numbers get the same 200 response.
    """
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
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)