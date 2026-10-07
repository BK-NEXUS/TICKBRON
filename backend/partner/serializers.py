"""
Serializers for partner API endpoints.

This module contains serializers for property, room, rate, and availability
management scoped to hotel-owner accounts.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from common.money import SUPPORTED_BASE_CURRENCIES, is_whole_som
from common.storage import validate_image_file
from geography.serializers import GeographyRefsMixin
from properties.models import Property, RoomType, RatePlan, DateInventory, RoomInventory, RoomBlock, PropertyPhoto
from properties.serializers import (
    PropertyPhotoSerializer, AmenitySerializer, PropertyAmenitySerializer
)


def _check_price_unit(currency, amount, field):
    """UZS prices are whole so'm (R6)."""
    if currency == 'UZS' and amount is not None and not is_whole_som(amount):
        raise serializers.ValidationError({field: "UZS prices must be whole so'm."})


class PropertyCurrencyMixin:
    """
    R6: a property is priced in USD or UZS. Default: its country's currency when supported
    (Uzbekistan -> UZS), else USD. It cannot change once the property has room types,
    because every room type, rate plan and nightly price uses it.
    """

    def validate_currency(self, value):
        if value not in SUPPORTED_BASE_CURRENCIES:
            raise serializers.ValidationError(f"Currency must be one of: {', '.join(SUPPORTED_BASE_CURRENCIES)}.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if 'currency' not in attrs and self.instance is None:
            country = attrs.get('country_ref')
            country_currency = getattr(country, 'currency', None)
            attrs['currency'] = country_currency if country_currency in SUPPORTED_BASE_CURRENCIES else 'USD'
        currency = attrs.get('currency', getattr(self.instance, 'currency', None))
        if (self.instance is not None and currency != self.instance.currency
                and self.instance.room_types.filter(is_deleted=False).exists()):
            raise serializers.ValidationError(
                {'currency': 'The currency cannot change after room types exist; their prices use it.'})
        _check_price_unit(currency, attrs.get('base_price'), 'base_price')
        return attrs


class ChildCurrencyMixin:
    """
    R6: room types, rate plans and nightly prices use their property's currency. Omitted means
    the property's; anything else is rejected. `price_field` must be whole so'm for UZS.
    """
    price_field = 'base_price'

    def property_of(self, attrs):
        raise NotImplementedError

    def validate(self, attrs):
        attrs = super().validate(attrs)
        prop = self.property_of(attrs)
        if prop is not None:
            sent = attrs.get('currency')
            if sent is not None and sent != prop.currency:
                raise serializers.ValidationError(
                    {'currency': f'Must be the property currency ({prop.currency}).'})
            attrs['currency'] = prop.currency
            _check_price_unit(prop.currency, attrs.get(self.price_field), self.price_field)
        return attrs


class PartnerPropertySerializer(PropertyCurrencyMixin, GeographyRefsMixin, serializers.ModelSerializer):
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
        # status is set by admin moderation (approve/suspend), never by the owner. The text location
        # is derived from the Geography refs (English names); city / state / country are accepted as
        # DEPRECATED input and resolved to refs (geography.serializers.resolve_text_location).
        read_only_fields = ['id', 'owner', 'status', 'created_at', 'updated_at']
        extra_kwargs = {'city': {'required': False}, 'country': {'required': False}}
    
    def get_full_address(self, obj) -> str:
        """Get the full address as a string."""
        return obj.get_full_address()
    
    def get_name(self, obj) -> str:
        return obj.display_name()


class PartnerPropertyCreateSerializer(PropertyCurrencyMixin, GeographyRefsMixin, serializers.ModelSerializer):
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
            'city', 'state', 'country',  # DEPRECATED input: resolved to the refs
            'latitude', 'longitude', 'base_price', 'currency', 'total_area', 'floor_number',
            'has_elevator', 'has_parking', 'has_wifi', 'has_ac', 'has_heating'
        ]
        extra_kwargs = {'city': {'required': False}, 'country': {'required': False}}
    
    def create(self, validated_data):
        """Create property with owner set to authenticated user."""
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class PartnerRoomTypeSerializer(ChildCurrencyMixin, serializers.ModelSerializer):
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

    def property_of(self, attrs):
        return attrs.get('property') or getattr(self.instance, 'property', None)
    
    def validate_property(self, value):
        """Ensure the property belongs to the authenticated hotel-owner."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.owner != request.user:
                raise serializers.ValidationError(
                    "You can only manage room types for your own properties."
                )
        return value


class PartnerRatePlanSerializer(ChildCurrencyMixin, serializers.ModelSerializer):
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

    def property_of(self, attrs):
        room_type = attrs.get('room_type') or getattr(self.instance, 'room_type', None)
        return room_type.property if room_type else None
    
    def validate_room_type(self, value):
        """Ensure the room type belongs to a property owned by the authenticated hotel-owner."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.property.owner != request.user:
                raise serializers.ValidationError(
                    "You can only manage rate plans for your own properties."
                )
        return value


class PartnerDateInventorySerializer(ChildCurrencyMixin, serializers.ModelSerializer):
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

    price_field = 'price'

    def property_of(self, attrs):
        rate_plan = attrs.get('rate_plan') or getattr(self.instance, 'rate_plan', None)
        return rate_plan.room_type.property if rate_plan else None
    
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

    def validate(self, attrs):
        _check_price_unit(attrs['rate_plan'].room_type.property.currency, attrs.get('price'), 'price')
        return attrs


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
    can_report_no_show = serializers.BooleanField()
    report_deadline = serializers.DateField(allow_null=True)
