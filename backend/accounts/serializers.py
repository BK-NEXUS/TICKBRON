"""
Serializers for the accounts app.

This module contains serializers for favorites, reviews, notifications, and account history.
"""
from rest_framework import serializers
from bookings.models import Booking
from properties.serializers import PropertyTranslationSerializer
from .models import Favorite, Review, Notification, AccountHistory


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer for Favorite model.
    """
    property_city = serializers.CharField(source='property.city', read_only=True)
    property_country = serializers.CharField(source='property.country', read_only=True)
    property_base_price = serializers.DecimalField(source='property.base_price', read_only=True, max_digits=10, decimal_places=2)
    property_currency = serializers.CharField(source='property.currency', read_only=True)
    property_primary_photo = serializers.SerializerMethodField()
    # The property's name lives in its translations; FavoriteViewSet prefetches them
    property_translations = PropertyTranslationSerializer(
        source='property.translations', many=True, read_only=True
    )
    
    class Meta:
        model = Favorite
        fields = ['id', 'user', 'property', 'property_translations', 'property_city',
                  'property_country', 'property_base_price', 'property_currency', 
                  'property_primary_photo', 'notes', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
    
    def get_property_primary_photo(self, obj) -> str | None:
        """Get the primary photo for the property."""
        try:
            primary_photo = obj.property.photos.filter(is_primary=True, is_deleted=False).first()
            if primary_photo:
                return primary_photo.photo_url
        except:
            pass
        return None


class FavoriteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a favorite.
    """
    class Meta:
        model = Favorite
        fields = ['property', 'notes']
    
    def validate_property(self, value):
        """Validate that the property exists and is active."""
        if not value.is_active or value.is_deleted:
            raise serializers.ValidationError("Property is not available for favorites.")
        return value


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    property_city = serializers.CharField(source='property.city', read_only=True)
    property_country = serializers.CharField(source='property.country', read_only=True)
    booking_confirmation_code = serializers.CharField(source='booking.confirmation_code', read_only=True, allow_null=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'user_email', 'user_full_name', 'property', 'property_city', 
                  'property_country', 'booking', 'booking_confirmation_code', 'overall_rating',
                  'cleanliness_rating', 'location_rating', 'value_rating', 'amenities_rating', 
                  'service_rating', 'title', 'comment', 'status', 'reviewed_at', 'created_at']
        read_only_fields = ['id', 'user', 'status', 'reviewed_at', 'created_at']
    
    def validate_overall_rating(self, value):
        """Validate overall rating is between 1 and 5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Overall rating must be between 1 and 5.")
        return value
    
    def validate(self, attrs):
        """Validate category ratings if provided."""
        rating_fields = ['cleanliness_rating', 'location_rating', 'value_rating', 
                        'amenities_rating', 'service_rating']
        
        for field in rating_fields:
            if field in attrs and attrs[field] is not None:
                if not 1 <= attrs[field] <= 5:
                    raise serializers.ValidationError({field: f"{field} must be between 1 and 5."})
        
        return attrs


class ReviewUpdateSerializer(ReviewSerializer):
    """
    Serializer for editing a review. The booking and property are fixed at creation.
    """
    class Meta(ReviewSerializer.Meta):
        read_only_fields = ReviewSerializer.Meta.read_only_fields + ['property', 'booking']


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a review.
    """
    # A review is always tied to one of the reviewer's completed stays
    booking = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.all(), required=True, allow_null=False
    )

    class Meta:
        model = Review
        fields = ['property', 'booking', 'overall_rating', 'cleanliness_rating',
                  'location_rating', 'value_rating', 'amenities_rating', 'service_rating',
                  'title', 'comment']

    def validate_booking(self, value):
        """Validate that the booking belongs to the user, is completed and is not reviewed yet."""
        if value.guest != self.context['request'].user:
            raise serializers.ValidationError("You can only review your own bookings.")

        if value.status != 'completed':
            raise serializers.ValidationError("You can only review completed bookings.")

        # Soft-deleted reviews count too: they still hold the unique (user, booking) row
        if Review.objects.filter(booking=value).exists():
            raise serializers.ValidationError("This booking has already been reviewed.")

        return value

    def validate_property(self, value):
        """Validate that the property exists and is active."""
        if not value.is_active or value.is_deleted:
            raise serializers.ValidationError("Property is not available for review.")
        return value

    def validate(self, attrs):
        """Validate that the review is for the booked property."""
        if attrs['property'].id != attrs['booking'].property_id:
            raise serializers.ValidationError(
                {'property': "The review must be for the property of the booking."}
            )
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    property_name = serializers.CharField(source='property.display_name', read_only=True, allow_null=True)
    property_slug = serializers.CharField(source='property.slug', read_only=True, allow_null=True)
    booking_confirmation_code = serializers.CharField(source='booking.confirmation_code', read_only=True, allow_null=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'user', 'notification_type', 'priority', 'title', 'message',
                  'booking', 'booking_confirmation_code', 'property', 'property_name', 
                  'property_slug', 'is_read', 'read_at', 'sent_via_email', 'sent_via_sms',
                  'action_url', 'action_label', 'created_at']
        read_only_fields = ['id', 'user', 'sent_via_email', 'sent_via_sms', 'created_at']


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating notification read status.
    """
    class Meta:
        model = Notification
        fields = ['is_read']
    
    def validate_is_read(self, value):
        """Ensure read_at is set when marking as read."""
        if value and not self.instance.read_at:
            from django.utils import timezone
            self.instance.read_at = timezone.now()
        return value


class AccountHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for AccountHistory model.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    property_city = serializers.CharField(source='property.city', read_only=True, allow_null=True)
    booking_confirmation_code = serializers.CharField(source='booking.confirmation_code', read_only=True, allow_null=True)
    
    class Meta:
        model = AccountHistory
        fields = ['id', 'user', 'user_email', 'user_full_name', 'action', 'description',
                  'ip_address', 'user_agent', 'booking', 'booking_confirmation_code',
                  'property', 'property_city', 'metadata', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class AccountHistoryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating account history entries.
    """
    class Meta:
        model = AccountHistory
        fields = ['action', 'description', 'ip_address', 'user_agent', 
                  'booking', 'property', 'metadata']
