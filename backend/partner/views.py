"""
Views for partner API endpoints.

This module contains views for property, room, rate, and availability
management scoped to hotel-owner accounts.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from properties.models import Property, RoomType, RatePlan, DateInventory, PropertyPhoto
from bookings.models import Booking, BookingItem
from partner.serializers import (
    PartnerPropertySerializer, PartnerPropertyCreateSerializer,
    PartnerRoomTypeSerializer, PartnerRatePlanSerializer,
    PartnerDateInventorySerializer, PartnerPropertyPhotoSerializer,
    PartnerBookingSerializer
)


class IsHotelOwner(IsAuthenticated):
    """
    Custom permission to ensure user is a hotel-owner.
    
    Checks if the authenticated user has the hotel-owner role or staff status.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        # Allow staff users (super-admin and admin)
        if request.user.is_staff:
            return True
        
        # Check if user has hotel-owner role
        from permissions.models import Role
        if request.user.role and request.user.role.name == 'hotel-owner':
            return True
        
        return False


class PartnerPropertyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for property management by hotel-owners.
    
    Scoped to properties owned by the authenticated hotel-owner.
    """
    permission_classes = [IsHotelOwner]
    
    def get_queryset(self):
        """Filter queryset to properties owned by the authenticated user."""
        return Property.objects.filter(
            owner=self.request.user,
            is_deleted=False
        ).select_related('property_type')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PartnerPropertyCreateSerializer
        return PartnerPropertySerializer
    
    def perform_create(self, serializer):
        """Ensure owner is set to authenticated user."""
        serializer.save(owner=self.request.user)


class PartnerRoomTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for room type management by hotel-owners.
    
    Scoped to room types in properties owned by the authenticated hotel-owner.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerRoomTypeSerializer
    
    def get_queryset(self):
        """Filter queryset to room types in properties owned by the authenticated user."""
        return RoomType.objects.filter(
            property__owner=self.request.user,
            is_deleted=False
        ).select_related('property')


class PartnerRatePlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for rate plan management by hotel-owners.
    
    Scoped to rate plans in properties owned by the authenticated hotel-owner.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerRatePlanSerializer
    
    def get_queryset(self):
        """Filter queryset to rate plans in properties owned by the authenticated user."""
        return RatePlan.objects.filter(
            room_type__property__owner=self.request.user,
            is_deleted=False
        ).select_related('room_type__property')


class PartnerDateInventoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for date inventory management by hotel-owners.
    
    Scoped to date inventory in properties owned by the authenticated hotel-owner.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerDateInventorySerializer
    
    def get_queryset(self):
        """Filter queryset to date inventory in properties owned by the authenticated user."""
        return DateInventory.objects.filter(
            rate_plan__room_type__property__owner=self.request.user,
            is_deleted=False
        ).select_related('rate_plan__room_type__property')


@api_view(['POST'])
@permission_classes([IsHotelOwner])
def partner_property_photo_upload(request, property_id):
    """
    Upload a photo for a property.
    
    Path Parameters:
        property_id: Property ID
    
    Request Body:
        photo: Image file
        photo_type: Photo type (exterior, interior, amenity, room, other)
        caption: Photo caption (optional)
        is_primary: Whether this is the primary photo (optional)
        display_order: Display order (optional)
        alt_text: Alt text for accessibility (optional)
    
    Returns:
        Created property photo object
    """
    # Verify property ownership
    property = get_object_or_404(
        Property,
        id=property_id,
        owner=request.user,
        is_deleted=False
    )
    
    serializer = PartnerPropertyPhotoSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save(property=property)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_bookings(request):
    """
    List bookings for properties owned by the hotel-owner.
    
    Query Parameters:
        status: Filter by booking status (optional)
        payment_status: Filter by payment status (optional)
    
    Returns:
        List of bookings for the hotel-owner's properties
    """
    # Get bookings for properties owned by the hotel-owner
    booking_items = BookingItem.objects.filter(
        room_type__property__owner=request.user
    ).select_related('booking', 'room_type__property')
    
    booking_ids = booking_items.values_list('booking_id', flat=True).distinct()
    
    bookings = Booking.objects.filter(
        id__in=booking_ids,
        is_deleted=False
    )
    
    # Apply filters
    status_filter = request.query_params.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    payment_status_filter = request.query_params.get('payment_status')
    if payment_status_filter:
        bookings = bookings.filter(payment_status=payment_status_filter)
    
    # Serialize bookings
    bookings_data = []
    for booking in bookings:
        # Get property name from booking items
        booking_item = booking_items.filter(booking=booking).first()
        property_name = booking_item.room_type.property.city if booking_item else "Unknown"
        
        booking_data = {
            'id': booking.id,
            'guest_name': booking.guest_name,
            'property_name': property_name,
            'status': booking.status,
            'payment_status': booking.payment_status,
            'check_in': booking.check_in,
            'check_out': booking.check_out,
            'number_of_nights': booking.number_of_nights,
            'guest_count': booking.guest_count,
            'total_price': str(booking.total_price),
            'currency': booking.currency,
            'confirmation_code': booking.confirmation_code,
            'created_at': booking.created_at
        }
        bookings_data.append(booking_data)
    
    return Response(bookings_data, status=status.HTTP_200_OK)
