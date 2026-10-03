"""
Serializers for TICKBRON payment models.
"""
from django.utils import timezone
from rest_framework import serializers
from .models import PaymentTransaction, WebhookEvent, PaymentAuditLog


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentTransaction model.

    Output-only: transactions change only through the payment flow, and the
    payment method token is never returned.
    """

    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'idempotency_key', 'booking', 'provider',
            'provider_transaction_id', 'amount', 'currency',
            'status', 'provider_response',
            'error_code', 'error_message', 'client_ip', 'user_agent',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class PaymentTransactionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating payment transactions.

    client_ip and user_agent are taken from the request by the view, not from
    the body. Idempotency-key reuse is handled by the view, so the automatic
    unique validator is disabled here.
    """

    class Meta:
        model = PaymentTransaction
        fields = [
            'idempotency_key', 'booking', 'provider', 'amount',
            'currency', 'payment_method_token'
        ]
        extra_kwargs = {
            'idempotency_key': {'validators': []},
            'payment_method_token': {'write_only': True},
        }

    def validate_booking(self, value):
        """Only the booking's guest may pay for it; others see it as not found."""
        request = self.context.get('request')
        if request is None or value.guest_id != request.user.id:
            raise serializers.ValidationError('Booking not found.')
        return value

    def validate(self, attrs):
        """Validate payment transaction creation."""
        booking = attrs.get('booking')
        amount = attrs.get('amount')
        
        # Validate booking status
        if booking.status != 'pending':
            raise serializers.ValidationError(
                {'booking': 'Payment can only be initiated for pending bookings'}
            )
        
        # A pending booking past its payment window is about to be expired and
        # its rooms released; paying for it now would pay for rooms we may resell
        if booking.expires_at and booking.expires_at <= timezone.now():
            raise serializers.ValidationError(
                {'booking': 'Booking has expired; please create a new booking'}
            )
        
        # The guest pays the booking's charge snapshot (R6): UZS, fixed when the booking
        # was made. Client values are only compared, never used to compute anything.
        if amount != booking.charge_amount:
            raise serializers.ValidationError(
                {'amount': 'Payment amount must match the booking charge amount'}
            )

        # The amount alone is not enough: 300 UZS is not 300 USD
        if attrs.get('currency') != booking.charge_currency:
            raise serializers.ValidationError(
                {'currency': 'Payment currency must match the booking charge currency'}
            )

        return attrs


class WebhookEventSerializer(serializers.ModelSerializer):
    """
    Serializer for WebhookEvent model.
    """
    
    class Meta:
        model = WebhookEvent
        fields = [
            'id', 'provider', 'provider_event_id', 'payload', 
            'signature', 'signature_valid', 'timestamp', 
            'timestamp_valid', 'status', 'payment_transaction',
            'error_message', 'processed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'signature_valid', 'timestamp_valid', 
            'status', 'processed_at', 'created_at', 'updated_at'
        ]


class PaymentAuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentAuditLog model.
    """
    
    class Meta:
        model = PaymentAuditLog
        fields = [
            'id', 'payment_transaction', 'webhook_event', 'booking',
            'action', 'old_status', 'new_status', 'actor', 
            'ip_address', 'details', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at'
        ]