"""
accounts app ınıń serializer leri.

Bul modul favorit ler, sharhlar, bildiriwler hám akkaunt tariyxı serializer lerin óz ishine aladı.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from bookings.fields import OwnBookingField
from bookings.pricing import property_price_list, rate_lookup
from properties.serializers import PropertyTranslationSerializer
from .models import Favorite, Review, Notification, AccountHistory
from django.utils.translation import gettext as _


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Favorite modeli ushın serializer.
    """
    property_city = serializers.CharField(source='property.city', read_only=True)
    property_country = serializers.CharField(source='property.country', read_only=True)
    property_base_price = serializers.DecimalField(source='property.base_price', read_only=True, max_digits=10, decimal_places=2)
    property_currency = serializers.CharField(source='property.currency', read_only=True)
    property_primary_photo = serializers.SerializerMethodField()
    # R16: mehmanxananıń hár valyutadaǵı "dan" bahası, mehmanxana kartası sıyaqlı ({code: {amount, source}})
    property_prices = serializers.SerializerMethodField()
    # Mehmanxana atı onıń awdarmalarında saqlanadı; FavoriteViewSet olardı aldınan júklep aladı (prefetch)
    property_translations = PropertyTranslationSerializer(
        source='property.translations', many=True, read_only=True
    )

    class Meta:
        model = Favorite
        fields = ['id', 'user', 'property', 'property_translations', 'property_city',
                  'property_country', 'property_base_price', 'property_currency', 'property_prices',
                  'property_primary_photo', 'notes', 'created_at']
        # property jaratılǵanda belgilenedi: ózgertiw FavoriteCreateSerializer degi bos orın tekseriwin ótkizip jiberer edi
        read_only_fields = ['id', 'user', 'property', 'created_at']
        extra_kwargs = {'notes': {'max_length': 500}}

    def get_property_primary_photo(self, obj) -> str | None:
        """Tiykarǵı súwret URL i; dizim view si hár favorit ushın onı bir query menen júkleydi."""
        photos = obj.property.primary_photos if hasattr(obj.property, 'primary_photos') else obj.property.photos.filter(
            is_primary=True, is_deleted=False)
        photo = next(iter(photos), None)
        return photo.photo.url if photo and photo.photo else None

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_property_prices(self, obj):
        """Dizim view si hár favorittiń aktiv rate planların bir neshe query menen júkleydi; bahalar bir márte oqıladı."""
        if not hasattr(self, '_rate_of'):
            self._rate_of = rate_lookup(self.context.get('request'))
        plans = [plan for room_type in getattr(obj.property, 'card_room_types', []) for plan in room_type.rate_plans.all()]
        return property_price_list(obj.property, plans, self._rate_of)


class FavoriteCreateSerializer(serializers.ModelSerializer):
    """
    Favorit jaratıw ushın serializer.
    """
    class Meta:
        model = Favorite
        fields = ['property', 'notes']
        extra_kwargs = {'notes': {'max_length': 500}}

    def validate_property(self, value):
        """Mehmanxananıń járiyalanǵanın tekseredi."""
        if not value.is_active or value.is_deleted or value.status != 'active':
            raise serializers.ValidationError(_("Property is not available for favorites."))
        return value


def reviewer_label(user):
    """Sharh jazıwshı jámiyetshilikke qalay kórsetiledi: atı hám familiyasınıń birinshi háripi ("Aziz K."), hesh qashan mánzil
    emes."""
    # get_full_name() emes: atı bolmasa e-mail mánzilge túsip qaladı
    parts = (user.full_name or f'{user.first_name or ""} {user.last_name or ""}').split()
    if not parts:
        return ''
    return f'{parts[0]} {parts[-1][0]}.' if len(parts) > 1 else parts[0]


def stay_month(review):
    """Sharh qaysı turıwǵa tiyisli bolsa, sol ay (YYYY-MM), bron joq bolsa None."""
    return review.booking.check_out.strftime('%Y-%m') if review.booking_id else None


RATING_FIELDS = ['overall_rating', 'cleanliness_rating', 'location_rating', 'value_rating', 'amenities_rating',
                 'service_rating']


class PublicReviewSerializer(serializers.ModelSerializer):
    """Mehmanxana betine kirgen hár paydalanıwshı kóretuǵın tastıyıqlanǵan sharh."""
    reviewer = serializers.SerializerMethodField()
    stay_month = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'reviewer', 'stay_month', *RATING_FIELDS, 'title', 'comment', 'created_at', 'owner_reply', 'replied_at']

    def get_reviewer(self, review):
        return reviewer_label(review.user)

    def get_stay_month(self, review):
        return stay_month(review)


class ReviewSerializer(serializers.ModelSerializer):
    """
    Review modeli ushın serializer.
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
                  'service_rating', 'title', 'comment', 'status', 'reviewed_at', 'created_at', 'owner_reply', 'replied_at']
        read_only_fields = ['id', 'user', 'status', 'reviewed_at', 'created_at', 'owner_reply', 'replied_at']
        extra_kwargs = {'comment': {'max_length': 2000}}

    def validate_overall_rating(self, value):
        """Ulıwma bahanıń 1 hám 5 aralıǵında ekenin tekseredi."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError(_("Overall rating must be between 1 and 5."))
        return value

    def validate(self, attrs):
        """Kategoriya bahaların (berilgen bolsa) tekseredi."""
        rating_fields = ['cleanliness_rating', 'location_rating', 'value_rating',
                        'amenities_rating', 'service_rating']

        for field in rating_fields:
            if field in attrs and attrs[field] is not None:
                if not 1 <= attrs[field] <= 5:
                    raise serializers.ValidationError({field: f"{field} must be between 1 and 5."})

        return attrs


class ReviewUpdateSerializer(ReviewSerializer):
    """
    Sharhtı ózgertiw ushın serializer. Bron hám mehmanxana jaratılǵanda belgilenedi.
    """
    class Meta(ReviewSerializer.Meta):
        read_only_fields = ReviewSerializer.Meta.read_only_fields + ['property', 'booking']


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Sharh jaratıw ushın serializer.
    """
    # Sharh hárdaym sharh jazıwshınıń juwmaqlanǵan turıwlarınıń birine baylanǵan boladı
    booking = OwnBookingField(required=True, allow_null=False)

    class Meta:
        model = Review
        fields = ['property', 'booking', 'overall_rating', 'cleanliness_rating',
                  'location_rating', 'value_rating', 'amenities_rating', 'service_rating',
                  'title', 'comment']
        extra_kwargs = {'comment': {'max_length': 2000}}

    def validate_booking(self, value):
        """Bronnıń juwmaqlanǵanın hám ele sharh jazılmaǵanın tekseredi (iyesin OwnBookingField tekseredi)."""
        if value.status != 'completed':
            raise serializers.ValidationError(_("You can only review completed bookings."))

        # Óshirilgen (soft-deleted) sharhlar da esapqa alınadı: olar unique (user, booking) qatarın ele ustap turadı
        if Review.objects.filter(booking=value).exists():
            raise serializers.ValidationError(_("This booking has already been reviewed."))

        return value

    def validate_property(self, value):
        """Mehmanxananıń bar hám aktiv ekenin tekseredi."""
        if not value.is_active or value.is_deleted:
            raise serializers.ValidationError(_("Property is not available for review."))
        return value

    def validate(self, attrs):
        """Sharhtıń bronlanǵan mehmanxana ushın ekenin tekseredi."""
        if attrs['property'].id != attrs['booking'].property_id:
            raise serializers.ValidationError(
                {'property': _("The review must be for the property of the booking.")}
            )
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    """
    Notification modeli ushın serializer.
    """
    property_name = serializers.CharField(source='property.display_name', read_only=True, allow_null=True)
    property_slug = serializers.CharField(source='property.slug', read_only=True, allow_null=True)
    booking_confirmation_code = serializers.CharField(source='booking.confirmation_code', read_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = ['id', 'user', 'notification_type', 'priority', 'title', 'message', 'code', 'params',
                  'booking', 'booking_confirmation_code', 'property', 'property_name',
                  'property_slug', 'is_read', 'read_at', 'sent_via_email', 'sent_via_sms',
                  'action_url', 'action_label', 'created_at']
        read_only_fields = ['id', 'user', 'code', 'params', 'sent_via_email', 'sent_via_sms', 'created_at']


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """
    Bildiriwdiń oqılǵan statusın jańalaw ushın serializer.
    """
    class Meta:
        model = Notification
        fields = ['is_read']

    def validate_is_read(self, value):
        """Oqılǵan dep belgilengende read_at ornatılatuǵının támiyinleydi."""
        if value and not self.instance.read_at:
            from django.utils import timezone
            self.instance.read_at = timezone.now()
        return value


class AccountHistorySerializer(serializers.ModelSerializer):
    """
    AccountHistory modeli ushın serializer.
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
        read_only_fields = ['id', 'user', 'property', 'created_at']
