"""
Serializers for partner API endpoints.

This module contains serializers for property, room, rate, and availability
management scoped to hotel-owner accounts.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from common.storage import validate_image_file
from geography.serializers import GeographyRefsMixin
from properties.models import Property, RoomType, RatePlan, DateInventory, RoomInventory, RoomBlock, PropertyPhoto
from properties.serializers import (
    PropertyPhotoSerializer, AmenitySerializer, PropertyAmenitySerializer
)


class PartnerPropertySerializer(GeographyRefsMixin, serializers.ModelSerializer):
    """
    Serializer for property management by hotel-owners.
    
    Limited to properties owned by the authenticated hotel-owner.
    """
    full_address = serializers.SerializerMethodField()
    # Hotel name for the partner cards: English translation, else any, else the address
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'name', 'property_type', 'status', 'max_guests', 'bedrooms', 'bathrooms',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'country_ref', 'region_ref', 'city_ref',
            'latitude', 'longitude', 'base_price', 'currency', 'total_area', 'floor_number',
            'has_elevator', 'has_parking', 'has_wifi', 'has_ac', 'has_heating',
            'full_address', 'created_at', 'updated_at'
        ]
        # status is set by admin moderation (approve/suspend), never by the owner. The text
        # location is derived from the Geography refs (English names) and cannot be written.
        read_only_fields = ['id', 'owner', 'status', 'city', 'state', 'country', 'created_at', 'updated_at']
    
    def get_full_address(self, obj):
        """Get the full address as a string."""
        return obj.get_full_address()
    
    def get_name(self, obj):
        return obj.display_name()


class PartnerPropertyCreateSerializer(GeographyRefsMixin, serializers.ModelSerializer):
    """
    Serializer for creating new properties by hotel-owners.
    
    Owner is automatically set to the authenticated user.
    """
    class Meta:
        model = Property
        fields = [
            'property_type', 'max_guests', 'bedrooms', 'bathrooms',
            'address_line1', 'address_line2', 'postal_code',
            'country_ref', 'region_ref', 'city_ref',
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


class PartnerRoomInventorySerializer(serializers.ModelSerializer):
    """
    Serializer for room inventory (RoomInventory, audit #31) management by hotel-owners.

    This is the room type's real, shared physical room count -- the booking engine locks
    and updates it. DateInventory (PartnerDateInventorySerializer) still holds the price
    and each rate plan's own rules.
    """
    remaining_rooms = serializers.IntegerField(read_only=True)

    class Meta:
        model = RoomInventory
        fields = ['id', 'room_type', 'date', 'available_rooms', 'booked_rooms', 'remaining_rooms', 'is_available']
        read_only_fields = ['id', 'booked_rooms', 'remaining_rooms']

    def validate_room_type(self, value):
        """Ensure the room type belongs to a property owned by the authenticated hotel-owner."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.property.owner != request.user:
                raise serializers.ValidationError(
                    "You can only manage room inventory for your own properties."
                )
        return value

    def validate(self, data):
        """
        Mirror RoomInventory.clean(): available_rooms cannot exceed the room type's
        total_rooms. DRF's create/update flow never calls full_clean(), so this has to
        be enforced here too.
        """
        room_type = data.get('room_type') or (self.instance.room_type if self.instance else None)
        available_rooms = data.get(
            'available_rooms', self.instance.available_rooms if self.instance else None
        )
        if room_type is not None and available_rooms is not None and available_rooms > room_type.total_rooms:
            raise serializers.ValidationError({
                'available_rooms': f'Cannot be more than the {room_type.total_rooms} rooms of this room type.'
            })
        return data


class PartnerRoomInventoryBulkSerializer(serializers.Serializer):
    """
    Request body for POST /partner/room-inventory/bulk/ (3.6 calendar date-range edit):
    sets available_rooms and/or is_available for every night in [date_from, date_to).
    """
    room_type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.filter(is_deleted=False))
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    available_rooms = serializers.IntegerField(required=False, min_value=0)
    is_available = serializers.BooleanField(required=False)

    def validate_room_type(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.property.owner != request.user:
                raise serializers.ValidationError(
                    "You can only manage room inventory for your own properties."
                )
        return value


class PartnerDateInventoryBulkPriceSerializer(serializers.Serializer):
    """
    Request body for POST /partner/inventory/bulk-price/ (3.7 bulk price edit): sets the
    nightly price for one rate plan over every night in [date_from, date_to).
    """
    rate_plan = serializers.PrimaryKeyRelatedField(queryset=RatePlan.objects.filter(is_deleted=False))
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)

    def validate_rate_plan(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.room_type.property.owner != request.user:
                raise serializers.ValidationError(
                    "You can only manage inventory for your own properties."
                )
        return value


class PartnerBlockSerializer(serializers.ModelSerializer):
    """
    Serializer for external-booking blocks (RoomBlock, 3.5) by hotel-owners.

    Creating a block locks and decrements the affected RoomInventory rows
    (RoomBlock.create_block); it cannot push a night's room count below what is already
    booked on TICKBRON. Deleting a block restores them (release()).
    """
    class Meta:
        model = RoomBlock
        fields = ['id', 'room_type', 'date_from', 'date_to', 'rooms', 'note', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']

    def validate_room_type(self, value):
        """Ensure the room type belongs to a property owned by the authenticated hotel-owner."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.property.owner != request.user:
                raise serializers.ValidationError(
                    "You can only block room inventory for your own properties."
                )
        return value

    def create(self, validated_data):
        request = self.context['request']
        try:
            return RoomBlock.create_block(
                room_type=validated_data['room_type'],
                date_from=validated_data['date_from'],
                date_to=validated_data['date_to'],
                rooms=validated_data['rooms'],
                note=validated_data.get('note', ''),
                created_by=request.user,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)


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
