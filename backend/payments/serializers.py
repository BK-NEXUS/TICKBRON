"""
Serializers for TICKBRON payment models.
"""
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
        
        # Validate amount matches booking total
        if amount != booking.total_price:
            raise serializers.ValidationError(
                {'amount': 'Payment amount must match booking total'}
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