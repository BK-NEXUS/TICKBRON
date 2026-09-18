"""
Serializers for TICKBRON payment models.
"""
from rest_framework import serializers
from .models import PaymentTransaction, WebhookEvent, PaymentAuditLog


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentTransaction model.
    """
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'idempotency_key', 'booking', 'provider', 
            'provider_transaction_id', 'amount', 'currency', 
            'status', 'payment_method_token', 'provider_response',
            'error_code', 'error_message', 'client_ip', 'user_agent',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'provider_transaction_id', 'status', 
            'provider_response', 'error_code', 'error_message',
            'created_at', 'updated_at'
        ]


class PaymentTransactionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating payment transactions.
    """
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'idempotency_key', 'booking', 'provider', 'amount', 
            'currency', 'payment_method_token', 'client_ip', 'user_agent'
        ]
    
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