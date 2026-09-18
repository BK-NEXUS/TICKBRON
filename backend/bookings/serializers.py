"""
Serializers for TICKBRON booking endpoints.
"""
from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Booking, BookingItem


class BookingItemSerializer(serializers.ModelSerializer):
    """Serializer for booking items."""
    
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    rate_plan_name = serializers.CharField(source='rate_plan.name', read_only=True)
    
    class Meta:
        model = BookingItem
        fields = [
            'id', 'room_type', 'room_type_name', 'rate_plan', 'rate_plan_name',
            'number_of_rooms', 'price_per_night', 'currency'
        ]
        read_only_fields = ['id']


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for bookings."""
    
    booking_items = BookingItemSerializer(many=True, read_only=True)
    guest_name = serializers.CharField(source='guest.get_full_name', read_only=True)
    property_name = serializers.CharField(source='property.get_full_address', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'guest', 'guest_name', 'property', 'property_name',
            'status', 'payment_status', 'check_in', 'check_out',
            'number_of_nights', 'guest_count', 'total_price', 'currency',
            'special_requests', 'confirmation_code', 'cancelled_at',
            'cancellation_reason', 'expires_at', 'booking_items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'confirmation_code', 'cancelled_at', 'cancellation_reason',
            'expires_at', 'booking_items', 'created_at', 'updated_at'
        ]


class BookingCreateSerializer(serializers.Serializer):
    """Serializer for creating bookings with transaction-safe inventory locking."""
    
    property_id = serializers.IntegerField()
    room_type_id = serializers.IntegerField()
    rate_plan_id = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    guest_count = serializers.IntegerField(min_value=1)
    special_requests = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate booking creation parameters."""
        from properties.models import Property, RoomType, RatePlan
        
        # Validate date range
        if data['check_out'] <= data['check_in']:
            raise ValidationError({
                'check_out': 'Check-out date must be after check-in date'
            })
        
        # Validate property exists and is active
        try:
            property_obj = Property.objects.get(
                id=data['property_id'],
                is_active=True,
                is_deleted=False
            )
        except Property.DoesNotExist:
            raise ValidationError({
                'property_id': 'Property not found or not available'
            })
        
        # Validate room type exists and belongs to property
        try:
            room_type = RoomType.objects.get(
                id=data['room_type_id'],
                property=property_obj,
                is_deleted=False
            )
        except RoomType.DoesNotExist:
            raise ValidationError({
                'room_type_id': 'Room type not found or does not belong to this property'
            })
        
        # Validate rate plan exists and belongs to room type
        try:
            rate_plan = RatePlan.objects.get(
                id=data['rate_plan_id'],
                room_type=room_type,
                is_active=True,
                is_deleted=False
            )
        except RatePlan.DoesNotExist:
            raise ValidationError({
                'rate_plan_id': 'Rate plan not found or does not belong to this room type'
            })
        
        # Validate guest count against room type capacity
        if data['guest_count'] > room_type.max_occupancy:
            raise ValidationError({
                'guest_count': f'Guest count exceeds maximum occupancy of {room_type.max_occupancy}'
            })
        
        # Validate rate plan constraints
        number_of_nights = (data['check_out'] - data['check_in']).days
        
        if rate_plan.min_nights and number_of_nights < rate_plan.min_nights:
            raise ValidationError({
                'check_in': f'Booking duration is less than minimum nights requirement ({rate_plan.min_nights})'
            })
        
        if rate_plan.max_nights and number_of_nights > rate_plan.max_nights:
            raise ValidationError({
                'check_in': f'Booking duration exceeds maximum nights requirement ({rate_plan.max_nights})'
            })
        
        # Store validated objects for later use
        self.validated_objects = {
            'property': property_obj,
            'room_type': room_type,
            'rate_plan': rate_plan
        }
        
        return data
    
    def create(self, validated_data):
        """Create booking with transaction-safe inventory locking."""
        guest = self.context['request'].user
        property_obj = self.validated_objects['property']
        room_type = self.validated_objects['room_type']
        rate_plan = self.validated_objects['rate_plan']
        
        try:
            booking = Booking.create_booking(
                guest=guest,
                property_obj=property_obj,
                room_type=room_type,
                rate_plan=rate_plan,
                check_in=validated_data['check_in'],
                check_out=validated_data['check_out'],
                guest_count=validated_data['guest_count'],
                special_requests=validated_data.get('special_requests')
            )
            return booking
        except ValidationError as e:
            # Convert Django ValidationError to DRF ValidationError
            if hasattr(e, 'message_dict'):
                raise serializers.ValidationError(e.message_dict)
            else:
                raise serializers.ValidationError({'non_field_errors': str(e)})
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': f'Failed to create booking: {str(e)}'
            })


class BookingCancelSerializer(serializers.Serializer):
    """Serializer for cancelling bookings."""
    
    cancellation_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate cancellation parameters."""
        booking = self.context['booking']
        
        if booking.status in ['cancelled', 'completed', 'no_show']:
            raise ValidationError({
                'status': 'Booking cannot be cancelled in current status'
            })
        
        return data
    
    def update(self, instance, validated_data):
        """Cancel booking and restore inventory."""
        try:
            instance.cancel_booking(
                cancellation_reason=validated_data.get('cancellation_reason')
            )
            return instance
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': f'Failed to cancel booking: {str(e)}'
            })
