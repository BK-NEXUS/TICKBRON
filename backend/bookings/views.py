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
from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.conf import settings
from common.dates import business_today
from currency.rates import ExchangeRateUnavailable
from .models import Booking, BookingItem
from .serializers import BookingSerializer, BookingCreateSerializer, BookingCancelSerializer

logger = logging.getLogger('tickbron')

# Bookings are confirmed at once and paid in cash, so nothing stops a free account from taking rooms;
# without a cap one account could keep a whole hotel unavailable (also the old cap on unpaid holds)
# Owner decision 2026-10-23: one account holds at most two upcoming bookings, and their dates never overlap
MAX_UPCOMING_BOOKINGS_PER_GUEST = 2


class BookingCreateThrottle(UserRateThrottle):
    """Booking creation per user (settings: THROTTLE_BOOKING_CREATE_RATE)."""
    scope = 'booking_create'

    def allow_request(self, request, view):
        if settings.TESTING:
            return True
        return super().allow_request(request, view)


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
        ).select_related('guest', 'property').prefetch_related(
            # The item serializer names each room type and rate plan: fetch them with the items
            Prefetch('booking_items', queryset=BookingItem.objects.select_related('room_type', 'rate_plan')),
            'property__translations',
        )
    
    @staticmethod
    def _pending_cap_reached(user):
        """The guest already holds the most upcoming bookings (not cancelled, not arrived, not over)."""
        upcoming = Booking.objects.filter(
            guest=user, status__in=('pending', 'confirmed'), arrived_at__isnull=True,
            check_out__gte=business_today(), is_deleted=False,
        ).count()
        return upcoming >= MAX_UPCOMING_BOOKINGS_PER_GUEST

    @staticmethod
    def _pending_cap_response():
        return Response(
            {'error': 'Too many upcoming bookings. Cancel one or wait until you have stayed.',
             'code': 'too_many_upcoming_bookings'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    @staticmethod
    def _overlaps_another_stay(user, check_in, check_out):
        """The guest already has a live booking whose nights share a night with these dates (check-out day is free)."""
        return Booking.objects.filter(
            guest=user, status__in=('pending', 'confirmed'), is_deleted=False,
            check_in__lt=check_out, check_out__gt=check_in,
        ).exists()

    @staticmethod
    def _overlap_response():
        return Response(
            {'error': 'You already have a booking for these dates. Choose dates that start after it ends.',
             'code': 'overlapping_booking'},
            status=status.HTTP_409_CONFLICT
        )

    def _refused_by_account_rules(self, user, serializer):
        """The response when one account may not book these dates now, else None."""
        if self._pending_cap_reached(user):
            return self._pending_cap_response()
        if self._overlaps_another_stay(user, serializer.validated_data['check_in'], serializer.validated_data['check_out']):
            return self._overlap_response()
        return None

    def get_throttles(self):
        if self.action == 'create':
            return [BookingCreateThrottle()]
        return super().get_throttles()

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
        
        refused = self._refused_by_account_rules(request.user, serializer)
        if refused is not None:
            return refused

        try:
            with transaction.atomic():
                # Check the rules again under a lock on the guest's row: without it, parallel
                # requests all read the same bookings and every one of them passes the check above
                get_user_model().objects.select_for_update().get(pk=request.user.pk)
                refused = self._refused_by_account_rules(request.user, serializer)
                if refused is not None:
                    return refused
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
            body = {'error': 'Booking validation failed', 'details': e.detail}
            if getattr(e, 'reason', None):
                body['reason'] = e.reason
            return Response(body, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
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
        List the current user's bookings, newest first, 20 per page.

        Query parameters:
            status: Filter by status (optional)
            payment_status: Filter by payment status (optional)
            page: Page number (optional)

        Returns:
            { count, next, previous, results }
        """
        queryset = self.get_queryset().order_by('-created_at', '-id')

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        payment_status_filter = request.query_params.get('payment_status')
        if payment_status_filter:
            queryset = queryset.filter(payment_status=payment_status_filter)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def booking_cancel(request, booking_id):
    """
    Cancel a booking and restore inventory. Cancelling is always free: the guest pays cash at the hotel.
    
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
        return Response(BookingSerializer(updated_booking).data, status=status.HTTP_200_OK)
    except DRFValidationError as e:
        # BookingCancelSerializer.update() raises this for both business-rule
        # violations and unexpected internal errors; e.detail is already safe.
        return Response(
            {'error': 'Failed to cancel booking', 'details': e.detail},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception:
        logger.exception('Unexpected error cancelling booking')
        return Response(
            {'error': 'Failed to cancel booking'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
