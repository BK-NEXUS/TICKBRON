"""Sign in by SMS code, and proving that a phone number belongs to the signed-in user."""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.csrf import enforce_csrf
from common.request import get_client_ip
from common.security_log import log_security_event
from users.models import User
from users.serializers import ConfirmPhoneSerializer, RequestOTPSerializer, UserSerializer, VerifyOTPSerializer
from users.services import OTPService
from users.sessions import start_session
from users.throttles import (
    OTPDailyNumberThrottle, OTPRequestIPThrottle, OTPRequestRateThrottle, OTPVerifyRateThrottle,
    OwnNumberDailyThrottle, PhoneVerifyConfirmThrottle, PhoneVerifyDailyThrottle, PhoneVerifyRequestThrottle,
)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPRequestRateThrottle, OTPRequestIPThrottle, OTPDailyNumberThrottle])
def request_otp(request):
    """
    Send a login code to a phone number.

    Registered, unknown and locked numbers get the same 200 response. In test
    mode the code is returned in the response.
    """
    enforce_csrf(request)
    serializer = RequestOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    result = OTPService().send_otp(serializer.validated_data['phone_number'], client_ip=get_client_ip(request))
    return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPVerifyRateThrottle])
def verify_otp(request):
    """
    Check a login code and sign the user in like a password login does.

    Lock checks and failure counting happen inside OTPService.verify_otp; unknown
    numbers, wrong codes and locked accounts all get the same 400.
    """
    enforce_csrf(request)
    serializer = VerifyOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    client_ip = get_client_ip(request)
    result = OTPService().verify_otp(
        serializer.validated_data['phone_number'], serializer.validated_data['otp_code'], client_ip=client_ip
    )
    if not result['success']:
        log_security_event('otp_login_failed', request)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(id=result['user_id']).first()
    if user is None:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    start_session(request, user, client_ip, method='otp')
    return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


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
