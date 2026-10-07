"""
Serializers for the no-show report endpoints (R12 phase 3).

Owner rows carry the report, the booking reference and the hotel; staff rows add the exact
refund an approval would pay, the refunds already made and the abuse flag. No guest name,
phone or email in either: the staff see the booking reference and look the guest up the usual way.
"""
import re

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from bookings.models import NoShowReport

MIN_LENGTH, MAX_LENGTH = 10, 500
_HTML_TAG = re.compile(r'<\s*/?\s*[A-Za-z!][^>]*>')


class PlainTextComment(serializers.CharField):
    """10-500 characters of plain text after stripping; HTML tags are refused."""

    def __init__(self, **kwargs):
        kwargs.setdefault('min_length', MIN_LENGTH)
        kwargs.setdefault('max_length', MAX_LENGTH)
        kwargs.setdefault('trim_whitespace', True)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if data is not None and not isinstance(data, str):
            self.fail('invalid')
        value = super().to_internal_value(data)
        if _HTML_TAG.search(value):
            raise serializers.ValidationError('HTML is not allowed.')
        return value


class ReportCommentSerializer(serializers.Serializer):
    comment = PlainTextComment()


class DecisionSerializer(serializers.Serializer):
    decision_comment = PlainTextComment()


class OwnerReportSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source='booking.confirmation_code', read_only=True)
    property_name = serializers.SerializerMethodField()
    check_in = serializers.DateField(source='booking.check_in', read_only=True)
    check_out = serializers.DateField(source='booking.check_out', read_only=True)

    class Meta:
        model = NoShowReport
        fields = ['id', 'booking_id', 'booking_reference', 'property_id', 'property_name', 'check_in',
                  'check_out', 'comment', 'status', 'decision_comment', 'decided_at', 'created_at']
        read_only_fields = fields

    def get_property_name(self, obj) -> str:
        return obj.property.display_name()


class StaffReportSerializer(OwnerReportSerializer):
    """Context: flagged (set of property ids), previews ({booking id: preview}), refunds ({booking id: [rows]})."""
    hotel_flagged = serializers.SerializerMethodField()
    refund_preview = serializers.SerializerMethodField()
    refunds = serializers.SerializerMethodField()

    class Meta(OwnerReportSerializer.Meta):
        fields = OwnerReportSerializer.Meta.fields + [
            'decided_by_id', 'created_by_id', 'hotel_flagged', 'refund_preview', 'refunds']
        read_only_fields = fields

    def get_hotel_flagged(self, obj) -> bool:
        return obj.property_id in self.context.get('flagged', ())

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_refund_preview(self, obj):
        # Only a pending report still has a refund to preview; a decided one shows `refunds`
        if obj.status != 'pending':
            return None
        return self.context.get('previews', {}).get(obj.booking_id)

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_refunds(self, obj):
        return self.context.get('refunds', {}).get(obj.booking_id, [])
