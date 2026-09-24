"""
Serializers for partner API endpoints.

This module contains serializers for property, room, rate, and availability
management scoped to hotel-owner accounts.
"""
from rest_framework import serializers
from common.storage import validate_image_file
from properties.models import Property, RoomType, RatePlan, DateInventory, PropertyPhoto
from properties.serializers import (
    PropertyPhotoSerializer, AmenitySerializer, PropertyAmenitySerializer
)


class PartnerPropertySerializer(serializers.ModelSerializer):
    """
    Serializer for property management by hotel-owners.
    
    Limited to properties owned by the authenticated hotel-owner.
    """
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'property_type', 'status', 'max_guests', 'bedrooms', 'bathrooms',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'latitude', 'longitude', 'base_price', 'currency', 'total_area', 'floor_number',
            'has_elevator', 'has_parking', 'has_wifi', 'has_ac', 'has_heating',
            'full_address', 'created_at', 'updated_at'
        ]
        # status is set by admin moderation (approve/suspend), never by the owner
        read_only_fields = ['id', 'owner', 'status', 'created_at', 'updated_at']
    
    def get_full_address(self, obj):
        """Get the full address as a string."""
        return obj.get_full_address()


class PartnerPropertyCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new properties by hotel-owners.
    
    Owner is automatically set to the authenticated user.
    """
    class Meta:
        model = Property
        fields = [
            'property_type', 'max_guests', 'bedrooms', 'bathrooms',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'latitude', 'longitude', 'base_price', 'currency', 'total_area', 'floor_number',
            'has_elevator', 'has_parking', 'has_wifi', 'has_ac', 'has_heating'
        ]
    
    def create(self, validated_data):
        """Create property with owner set to authenticated user."""
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class PartnerRoomTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for room type management by hotel-owners.
    
    Limited to room types in properties owned by the authenticated hotel-owner.
    """
    class Meta:
        model = RoomType
        fields = [
            'id', 'property', 'name', 'slug', 'description', 'base_occupancy', 'max_occupancy',
            'base_price', 'currency', 'total_rooms', 'bed_configuration', 'room_size'
        ]
        read_only_fields = ['id']
    
    def validate_property(self, value):
        """Ensure the property belongs to the authenticated hotel-owner."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.owner != request.user:
                raise serializers.ValidationError(
                    "You can only manage room types for your own properties."
                )
        return value


class PartnerRatePlanSerializer(serializers.ModelSerializer):
    """
    Serializer for rate plan management by hotel-owners.
    
    Limited to rate plans in properties owned by the authenticated hotel-owner.
    """
    class Meta:
        model = RatePlan
        fields = [
            'id', 'room_type', 'name', 'slug', 'rate_type', 'description', 'base_price',
            'currency', 'min_nights', 'max_nights', 'is_active', 'cancellation_policy',
            'deposit_required', 'deposit_percentage', 'advance_booking_days'
        ]
        read_only_fields = ['id']
    
    def validate_room_type(self, value):
        """Ensure the room type belongs to a property owned by the authenticated hotel-owner."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.property.owner != request.user:
                raise serializers.ValidationError(
                    "You can only manage rate plans for your own properties."
                )
        return value


class PartnerDateInventorySerializer(serializers.ModelSerializer):
    """
    Serializer for date inventory management by hotel-owners.
    
    Limited to date inventory in properties owned by the authenticated hotel-owner.
    """
    remaining_rooms = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = DateInventory
        fields = [
            'id', 'rate_plan', 'date', 'available_rooms', 'booked_rooms', 'remaining_rooms',
            'price', 'currency', 'is_available', 'minimum_stay', 'maximum_stay', 'notes'
        ]
        read_only_fields = ['id', 'booked_rooms', 'remaining_rooms']
    
    def validate_rate_plan(self, value):
        """Ensure the rate plan belongs to a property owned by the authenticated hotel-owner."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.room_type.property.owner != request.user:
                raise serializers.ValidationError(
                    "You can only manage inventory for your own properties."
                )
        return value


class PartnerPropertyPhotoSerializer(serializers.ModelSerializer):
    """
    Serializer for property photo management by hotel-owners.
    
    Limited to photos in properties owned by the authenticated hotel-owner.
    """
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyPhoto
        fields = [
            'id', 'photo', 'photo_url', 'photo_type', 'caption', 'is_primary',
            'display_order', 'alt_text'
        ]
        read_only_fields = ['id']
    
    def get_photo_url(self, obj):
        """Get the absolute URL for the photo."""
        if obj.photo:
            return obj.photo.url
        return None

    def validate_photo(self, value):
        """
        Enforce the size/extension/content-type rules from model.clean() here too,
        since DRF's create/update flow never calls full_clean().
        """
        is_valid, error_message = validate_image_file(value)
        if not is_valid:
            raise serializers.ValidationError(error_message)
        return value

    def validate_property(self, value):
        """Ensure the property belongs to the authenticated hotel-owner."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.owner != request.user:
                raise serializers.ValidationError(
                    "You can only manage photos for your own properties."
                )
        return value


class PartnerBookingSerializer(serializers.Serializer):
    """
    Serializer for partner booking listing.
    
    Shows bookings for properties owned by the hotel-owner.
    """
    id = serializers.IntegerField()
    guest_name = serializers.CharField()
    property_name = serializers.CharField()
    status = serializers.CharField()
    payment_status = serializers.CharField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    number_of_nights = serializers.IntegerField()
    guest_count = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    confirmation_code = serializers.CharField()
    created_at = serializers.DateTimeField()
