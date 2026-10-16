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
from users import lockout
from users.models import User
from users.serializers import UserLoginSerializer, UserRegistrationSerializer, UserSerializer
from users.sessions import start_session
from users.throttles import LoginRateThrottle, RegisterRateThrottle

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
    """Create an account from e-mail, name and password, and sign the new user in."""
    enforce_csrf(request)
    serializer = UserRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()
    login(request, user)
    log_security_event('account_created', request, user=user, level=logging.INFO)
    record_history(user, 'account_created', request)
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


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

    start_session(request, authenticated_user, client_ip, method='password')
    return Response(UserSerializer(authenticated_user).data, status=status.HTTP_200_OK)


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
    return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


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
