"""
Views for TICKBRON booking endpoints.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .models import Booking
from .serializers import BookingSerializer, BookingCreateSerializer, BookingCancelSerializer


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for booking management.
    
    Provides CRUD operations for bookings with proper authentication and permissions.
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return bookings for the current user."""
        return Booking.objects.filter(
            guest=self.request.user,
            is_deleted=False
        ).select_related('guest', 'property').prefetch_related('booking_items')
    
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
        except ValidationError as e:
            # Handle Django ValidationError
            return Response(
                {'error': 'Booking validation failed', 'details': e.message_dict},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Handle other exceptions - check if it's a validation-like error
            error_str = str(e)
            if 'availability' in error_str or 'validation' in error_str.lower():
                return Response(
                    {'error': 'Booking validation failed', 'details': error_str},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'error': 'Failed to create booking', 'details': str(e)},
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
    except Exception as e:
        return Response(
            {'error': 'Failed to cancel booking', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
