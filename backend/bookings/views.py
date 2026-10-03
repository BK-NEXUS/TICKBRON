"""
Views for TICKBRON booking endpoints.
"""
import logging
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from currency.rates import ExchangeRateUnavailable
from .models import Booking
from .serializers import BookingSerializer, BookingCreateSerializer, BookingCancelSerializer

logger = logging.getLogger('tickbron')


class BookingViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    """
    ViewSet for booking management.
    
    Supports create, list and retrieve only. Bookings are never updated or
    deleted directly by guests: status changes go through the state machine
    (e.g. the cancel endpoint), so PUT/PATCH/DELETE return 405.
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return bookings for the current user."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema generation: no user
            return self.get_serializer_class().Meta.model.objects.none()
        return Booking.objects.filter(
            guest=self.request.user,
            is_deleted=False
        ).select_related('guest', 'property').prefetch_related('booking_items', 'property__translations')
    
    def create(self, request, *args, **kwargs):
        """
        Create a new booking with transaction-safe inventory locking.
        
        Request body:
            property_id: Property ID
            room_type_id: Room type ID
            rate_plan_id: Rate plan ID
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guest_count: Number of guests
            special_requests: Optional special requests text
        
        Returns:
            Created booking with confirmation code
        """
        serializer = BookingCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid booking parameters', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            booking = serializer.save()
            response_serializer = BookingSerializer(booking)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except ExchangeRateUnavailable as e:
            # USD-priced hotel and no rate yet: nothing was reserved (R6 decision A)
            return Response(
                {'error': 'Exchange rate unavailable', 'code': e.default_code, 'details': str(e.detail)},
                status=e.status_code
            )
        except ValidationError as e:
            # Handle Django ValidationError
            return Response(
                {'error': 'Booking validation failed', 'details': e.message_dict},
                status=status.HTTP_400_BAD_REQUEST
            )
        except DRFValidationError as e:
            # BookingCreateSerializer.create() raises this for both business-rule
            # violations and unexpected internal errors; either way e.detail is
            # already a safe, non-leaking message by the time it gets here.
            return Response(
                {'error': 'Booking validation failed', 'details': e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Truly unexpected error: never echo str(e) to the client.
            logger.exception('Unexpected error creating booking')
            return Response(
                {'error': 'Failed to create booking'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific booking.
        
        Path parameters:
            id: Booking ID
        
        Returns:
            Booking details
        """
        booking = self.get_object()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        """
        List all bookings for the current user.
        
        Query parameters:
            status: Filter by status (optional)
            payment_status: Filter by payment status (optional)
        
        Returns:
            List of bookings
        """
        queryset = self.get_queryset()
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        payment_status_filter = request.query_params.get('payment_status')
        if payment_status_filter:
            queryset = queryset.filter(payment_status=payment_status_filter)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def booking_cancel(request, booking_id):
    """
    Cancel a booking and restore inventory.
    
    Path parameters:
        booking_id: Booking ID
    
    Request body:
        cancellation_reason: Optional reason for cancellation
    
    Returns:
        Updated booking with cancelled status
    """
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        guest=request.user,
        is_deleted=False
    )
    
    serializer = BookingCancelSerializer(
        booking,
        data=request.data,
        partial=True,
        context={'booking': booking}
    )
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid cancellation parameters', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        updated_booking = serializer.save()
        response_serializer = BookingSerializer(updated_booking)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    except DRFValidationError as e:
        # BookingCancelSerializer.update() raises this for both business-rule
        # violations and unexpected internal errors; e.detail is already safe.
        return Response(
            {'error': 'Failed to cancel booking', 'details': e.detail},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.exception('Unexpected error cancelling booking')
        return Response(
            {'error': 'Failed to cancel booking'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
