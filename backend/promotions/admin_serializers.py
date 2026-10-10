from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from geography.models import City, Country, Region
from promotions import service
from promotions.models import Promotion
from properties.models import Property


class PromotionWriteFields(serializers.Serializer):
    """Input shared by create and update. Status, payment and hotel are never writable here."""
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    priority = serializers.IntegerField()
    country_ref = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.filter(is_deleted=False), allow_null=True)
    region_ref = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.filter(is_deleted=False), allow_null=True)
    city_ref = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.filter(is_deleted=False), allow_null=True)
    price_amount = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    price_currency = serializers.CharField(max_length=3)
    note = serializers.CharField(allow_blank=True, trim_whitespace=False)


class PromotionCreateSerializer(PromotionWriteFields):
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.filter(is_deleted=False))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('priority', 'country_ref', 'region_ref', 'city_ref', 'price_amount', 'price_currency', 'note'):
            self.fields[name].required = False


class PromotionUpdateSerializer(PromotionWriteFields):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default='')


class PromotionSerializer(serializers.ModelSerializer):
    property = serializers.SerializerMethodField()
    paid = serializers.SerializerMethodField()
    is_shown_now = serializers.SerializerMethodField()
    blocked_reason = serializers.SerializerMethodField()
    total_impressions = serializers.SerializerMethodField()
    total_clicks = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = [
            'id', 'property', 'start_date', 'end_date', 'priority', 'country_ref', 'region_ref', 'city_ref',
            'price_amount', 'price_currency', 'note', 'paid', 'paid_at', 'status', 'cancelled_reason',
            'is_shown_now', 'blocked_reason', 'total_impressions', 'total_clicks', 'created_at',
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.DictField())
    def get_property(self, obj):
        prop = obj.property
        return {'id': prop.pk, 'name': prop.display_name(), 'city': prop.city, 'status': prop.status}

    @extend_schema_field(serializers.BooleanField())
    def get_paid(self, obj):
        return obj.paid_at is not None

    @extend_schema_field(serializers.BooleanField())
    def get_is_shown_now(self, obj):
        return service.is_shown_now(obj)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_blocked_reason(self, obj):
        return service.blocked_reason(obj)

    def _total(self, obj, annotated, column):
        value = getattr(obj, annotated, None)
        if value is None:
            value = sum(getattr(day, column) for day in obj.daily_stats.all())
        return value

    @extend_schema_field(serializers.IntegerField())
    def get_total_impressions(self, obj):
        return self._total(obj, 'sum_impressions', 'impressions')

    @extend_schema_field(serializers.IntegerField())
    def get_total_clicks(self, obj):
        return self._total(obj, 'sum_clicks', 'clicks')
