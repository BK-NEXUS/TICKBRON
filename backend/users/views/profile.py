"""The signed-in user's own profile and session."""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.serializers import UserSerializer, UserUpdateSerializer


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def me(request):
    """The profile of the signed-in user."""
    if request.user.is_authenticated:
        return Response(UserSerializer(request.user).data)
    return Response(
        {'detail': 'Authentication credentials were not provided.'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Change name, phone number and contact preferences (whatsapp, telegram, preferred_contact_method)."""
    serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_session(request):
    """Tell the SPA whether the current session is still valid, and who it belongs to."""
    if request.user.is_authenticated:
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
    return Response({'detail': 'No active session found.'}, status=status.HTTP_401_UNAUTHORIZED)
