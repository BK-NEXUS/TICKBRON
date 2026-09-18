"""
Webhook processing utilities for TICKBRON.

This module contains utilities for processing payment provider webhooks
with signature validation, replay protection, and idempotency.
"""
import json
import logging
import hashlib
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone
from django.conf import settings
from typing import Dict, Optional, Tuple
from .adapters import get_payment_adapter, SignatureValidationError
from .models import WebhookEvent, PaymentTransaction, PaymentAuditLog

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Webhook processor for handling payment provider webhooks.
    
    Implements signature validation, replay protection, and idempotency.
    """
    
    def __init__(self, provider: str):
        """
        Initialize webhook processor for a specific provider.
        
        Args:
            provider: Payment provider name ('payme', 'click', 'visa')
        """
        self.provider = provider.lower()
        self.adapter = get_payment_adapter(provider)
    
    def process_webhook(self, payload: Dict[str, any], signature: str,
                       headers: Optional[Dict[str, str]] = None) -> Tuple[WebhookEvent, bool]:
        """
        Process a webhook from a payment provider.
        
        Args:
            payload: Webhook payload from provider
            signature: Signature from provider
            headers: HTTP headers (optional, for additional validation)
        
        Returns:
            tuple: (webhook_event, is_new) where is_new is True if this is a new webhook
        
        Raises:
            SignatureValidationError: If signature validation fails
            ValueError: If webhook is a replay attack
        """
        # Extract provider event ID
        provider_event_id = self._extract_event_id(payload)
        
        # Check for replay attack
        if self._is_replay_attack(provider_event_id):
            logger.warning(f"Replay attack detected for event {provider_event_id}")
            raise ValueError(f"Replay attack detected for event {provider_event_id}")
        
        # Create webhook event record
        webhook_event = WebhookEvent.objects.create(
            provider=self.provider,
            provider_event_id=provider_event_id,
            payload=payload,
            signature=signature,
            status='received'
        )
        
        try:
            # Verify signature
            is_valid = self.adapter.verify_webhook_signature(payload, signature)
            webhook_event.signature_valid = is_valid
            
            if not is_valid:
                webhook_event.status = 'invalid_signature'
                webhook_event.error_message = 'Invalid webhook signature'
                webhook_event.save()
                raise SignatureValidationError("Invalid webhook signature")
            
            # Validate timestamp
            timestamp = self._extract_timestamp(payload)
            webhook_event.timestamp = timestamp
            
            if timestamp and not self.adapter.validate_timestamp(timestamp):
                webhook_event.timestamp_valid = False
                webhook_event.status = 'invalid_signature'
                webhook_event.error_message = 'Webhook timestamp too old'
                webhook_event.save()
                raise SignatureValidationError("Webhook timestamp too old")
            
            webhook_event.timestamp_valid = True
            
            # Process webhook with adapter
            processed_data = self.adapter.process_webhook(payload, signature)
            
            # Update webhook event with processed data
            webhook_event.status = 'processed'
            webhook_event.processed_at = timezone.now()
            
            # Link to payment transaction if possible
            payment_transaction = self._link_to_payment_transaction(processed_data)
            if payment_transaction:
                webhook_event.payment_transaction = payment_transaction
            
            webhook_event.save()
            
            # Create audit log
            PaymentAuditLog.log_action(
                action='webhook_processed',
                webhook_event=webhook_event,
                payment_transaction=payment_transaction,
                details={'processed_data': self._serialize_for_json(processed_data)}
            )
            
            return webhook_event, True
            
        except SignatureValidationError as e:
            # Log the error
            PaymentAuditLog.log_action(
                action='webhook_received',
                webhook_event=webhook_event,
                details={'error': str(e)}
            )
            raise
        except Exception as e:
            # Handle other errors
            webhook_event.status = 'failed'
            webhook_event.error_message = str(e)
            webhook_event.save()
            
            PaymentAuditLog.log_action(
                action='webhook_received',
                webhook_event=webhook_event,
                details={'error': str(e)}
            )
            logger.error(f"Webhook processing error: {e}")
            raise
    
    def _extract_event_id(self, payload: Dict[str, any]) -> str:
        """
        Extract provider event ID from payload.
        
        Args:
            payload: Webhook payload
        
        Returns:
            str: Provider event ID
        """
        # Different providers use different field names
        event_id_fields = ['id', 'event_id', 'payment_id', 'transaction_id', 'webhook_id']
        
        for field in event_id_fields:
            if field in payload:
                return str(payload[field])
        
        # Fallback to hash of payload if no ID found
        payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        return f"unknown_{payload_hash[:16]}"
    
    def _extract_timestamp(self, payload: Dict[str, any]) -> Optional[datetime]:
        """
        Extract timestamp from payload.
        
        Args:
            payload: Webhook payload
        
        Returns:
            datetime: Timestamp or None if not found
        """
        timestamp_fields = ['timestamp', 'created_at', 'event_time', 'date']
        
        for field in timestamp_fields:
            if field in payload:
                timestamp_value = payload[field]
                try:
                    # Handle different timestamp formats
                    if isinstance(timestamp_value, (int, float)):
                        # Unix timestamp
                        return datetime.fromtimestamp(timestamp_value, tz=dt_timezone.utc)
                    elif isinstance(timestamp_value, str):
                        # ISO format string
                        return datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _is_replay_attack(self, provider_event_id: str) -> bool:
        """
        Check if this is a replay attack.
        
        Args:
            provider_event_id: Provider event ID
        
        Returns:
            bool: True if this is a replay attack
        """
        return WebhookEvent.objects.filter(
            provider=self.provider,
            provider_event_id=provider_event_id
        ).exists()
    
    def _link_to_payment_transaction(self, processed_data: Dict[str, any]) -> Optional[PaymentTransaction]:
        """
        Link webhook to payment transaction if possible.
        
        Args:
            processed_data: Processed webhook data
        
        Returns:
            PaymentTransaction: Linked transaction or None
        """
        provider_transaction_id = processed_data.get('provider_transaction_id')
        if provider_transaction_id:
            try:
                return PaymentTransaction.objects.get(
                    provider_transaction_id=provider_transaction_id
                )
            except PaymentTransaction.DoesNotExist:
                pass
        
        return None
    
    def _serialize_for_json(self, data: any) -> any:
        """
        Serialize data for JSON storage, handling datetime objects.
        
        Args:
            data: Data to serialize
        
        Returns:
            JSON-serializable data
        """
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {k: self._serialize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_for_json(item) for item in data]
        else:
            return data


def validate_webhook_request(request) -> Tuple[Dict[str, any], str]:
    """
    Validate and extract webhook data from HTTP request.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        tuple: (payload, signature)
    
    Raises:
        ValueError: If request is invalid
    """
    # Check content type
    content_type = request.content_type
    if 'application/json' not in content_type:
        raise ValueError(f"Invalid content type: {content_type}")
    
    # Parse JSON payload
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON payload: {e}")
    
    # Extract signature from headers
    signature = request.headers.get('X-Signature') or request.headers.get('X-Webhook-Signature')
    if not signature:
        raise ValueError("Missing signature header")
    
    return payload, signature


def get_webhook_processor(provider: str) -> WebhookProcessor:
    """
    Factory function to get webhook processor for a provider.
    
    Args:
        provider: Payment provider name
    
    Returns:
        WebhookProcessor: Webhook processor instance
    """
    return WebhookProcessor(provider)