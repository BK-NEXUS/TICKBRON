"""
Views for user authentication and management.

This module contains views for user registration, login, and session management.
"""
import sys
import os
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.contrib.auth import authenticate, login, logout
from users.models import User
from users.serializers import UserSerializer, UserRegistrationSerializer, UserLoginSerializer, RequestOTPSerializer, VerifyOTPSerializer, UserUpdateSerializer
from users.services import OTPService

# Check if running in test mode
TESTING = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST')


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


class OTPRequestRateThrottle(AnonRateThrottle):
    """Rate throttle for OTP request endpoint - 3 requests per minute per phone number."""
    rate = '3/min'
    scope = 'otp_request'

    def get_cache_key(self, request, view):
        """
        Use phone number as cache key for rate limiting per phone number.
        """
        phone_number = request.data.get('phone_number', '')
        if phone_number:
            return f'otp_request_{phone_number}'
        return super().get_cache_key(request, view)

    def allow_request(self, request, view):
        # Disable throttling during tests
        if TESTING:
            return True
        return super().allow_request(request, view)


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


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    """
    Login user with email and password.
    
    Authenticates user and creates a session using secure cookies.
    Includes account lockout protection after failed login attempts.
    """
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            user = User.objects.get(email=email)
            
            # Check if account is locked
            if user.is_account_locked():
                return Response(
                    {'detail': 'Account is temporarily locked due to too many failed login attempts. Please try again later.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Authenticate user
            authenticated_user = authenticate(request, username=email, password=password)
            if authenticated_user is not None and authenticated_user.is_active:
                # Reset failed login attempts on successful login
                authenticated_user.reset_failed_login()
                
                # Store login IP
                authenticated_user.last_login_ip = get_client_ip(request)
                authenticated_user.save()
                
                login(request, authenticated_user)
                return Response(
                    UserSerializer(authenticated_user).data,
                    status=status.HTTP_200_OK
                )
            else:
                # Increment failed login attempts
                user.increment_failed_login()
                return Response(
                    {'detail': 'Invalid credentials or account inactive.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except User.DoesNotExist:
            return Response(
                {'detail': 'Invalid credentials or account inactive.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


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


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPRequestRateThrottle])
def request_otp(request):
    """
    Request OTP code for phone-based authentication.
    
    Generates and sends an OTP code to the provided phone number.
    In test mode, the OTP code is returned in the response.
    Rate-limited to 3 requests per minute per phone number.
    """
    serializer = RequestOTPSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        
        otp_service = OTPService()
        result = otp_service.send_otp(phone_number)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    Verify OTP code and establish session.
    
    Verifies the OTP code for the provided phone number.
    On successful verification, establishes a session using the same
    mechanism as password login.
    """
    serializer = VerifyOTPSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']
        
        otp_service = OTPService()
        result = otp_service.verify_otp(phone_number, otp_code)
        
        if result['success']:
            try:
                user = User.objects.get(id=result['user_id'])
                
                # Check if account is locked
                if user.is_account_locked():
                    return Response(
                        {'detail': 'Account is temporarily locked due to too many failed login attempts. Please try again later.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Reset failed login attempts on successful login
                user.reset_failed_login()
                
                # Store login IP
                user.last_login_ip = get_client_ip(request)
                user.save()
                
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
        else:
            # Increment failed login attempts for invalid OTP
            try:
                user = User.objects.get(phone_number=phone_number)
                user.increment_failed_login()
            except User.DoesNotExist:
                pass
            
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)