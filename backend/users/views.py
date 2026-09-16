"""
Views for user authentication and management.

This module contains views for user registration, login, and session management.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from users.serializers import UserSerializer, UserRegistrationSerializer, UserLoginSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
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
def login_view(request):
    """
    Login user with email and password.
    
    Authenticates user and creates a session using secure cookies.
    """
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=email, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_200_OK
            )
        return Response(
            {'detail': 'Invalid credentials or account inactive.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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