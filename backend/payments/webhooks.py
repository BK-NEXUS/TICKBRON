"""
Webhook processing utilities for TICKBRON.

This module contains utilities for processing payment provider webhooks
with signature validation, replay protection, and idempotency.
"""
import json
import logging
import hashlib
import uuid
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.conf import settings
from typing import Dict, Optional, Tuple
from .adapters import get_payment_adapter, SignatureValidationError
from bookings.models import Booking
from .models import WebhookEvent, PaymentTransaction, PaymentAuditLog

logger = logging.getLogger(__name__)

# Provider statuses as delivered by our adapters' process_webhook(). The real
# Payme/Click vocabularies must be mapped here when production integration lands.
PROVIDER_SUCCESS_STATUSES = {'completed', 'success', 'paid'}
PROVIDER_FAILURE_STATUSES = {'failed', 'cancelled', 'canceled', 'error'}


class WebhookNotConfiguredError(Exception):
    """Raised when a provider's webhook secret is missing, so no webhook can be trusted."""


class WebhookNotSupportedError(Exception):
    """Raised for providers whose webhook handling is not implemented yet."""


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
            WebhookNotConfiguredError: If the provider's webhook secret is not set
            WebhookNotSupportedError: If the provider has no webhook handling yet
            SignatureValidationError: If signature or timestamp validation fails
        
        A replay of an already recorded event returns (existing_event, False).
        """
        # Fail closed: without a configured secret no signature can be trusted
        if not self.adapter.has_webhook_secret():
            logger.error(f"Webhook secret not configured for {self.provider}; rejecting webhook")
            raise WebhookNotConfiguredError(f"Webhook secret not configured for {self.provider}")

        # Extract provider event ID
        provider_event_id = self._extract_event_id(payload)

        # Verify the signature BEFORE recording the event under its ID. Otherwise
        # an unsigned request could claim a real event ID and get the genuine
        # webhook rejected as a replay later.
        try:
            is_valid = self.adapter.verify_webhook_signature(payload, signature)
        except NotImplementedError:
            raise WebhookNotSupportedError(f"Webhooks are not supported for {self.provider}")

        if not is_valid:
            self._record_invalid_signature(payload, signature, provider_event_id)
            raise SignatureValidationError("Invalid webhook signature")

        # Replay of an already recorded (validly signed) event: acknowledge it
        # without processing it again, so providers stop retrying
        existing_event = self._find_existing_event(provider_event_id)
        if existing_event is not None:
            logger.info(f"Webhook event {provider_event_id} already processed")
            return existing_event, False

        try:
            with transaction.atomic():
                webhook_event = WebhookEvent.objects.create(
                    provider=self.provider,
                    provider_event_id=provider_event_id,
                    payload=payload,
                    signature=signature,
                    signature_valid=True,
                    status='received'
                )
        except IntegrityError:
            # A concurrent delivery of the same event won the race
            return self._find_existing_event(provider_event_id), False

        try:
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
            
            # Link to payment transaction if possible, then apply the outcome
            payment_transaction = self._link_to_payment_transaction(processed_data)
            if payment_transaction:
                webhook_event.payment_transaction = payment_transaction
                self._apply_payment_status(payment_transaction, processed_data, webhook_event)

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
    
    def _find_existing_event(self, provider_event_id: str) -> Optional[WebhookEvent]:
        """
        Return the already recorded event with this ID, if any.

        Only validly signed events are stored under their real provider ID,
        so a match means the same genuine webhook was delivered again.
        """
        return WebhookEvent.objects.filter(
            provider=self.provider,
            provider_event_id=provider_event_id
        ).first()

    def _record_invalid_signature(self, payload: Dict[str, any], signature: str,
                                  claimed_event_id: str) -> WebhookEvent:
        """
        Keep a record of a rejected webhook for security monitoring.

        It is stored under a synthetic ID so it never occupies the real
        provider event ID.
        """
        webhook_event = WebhookEvent.objects.create(
            provider=self.provider,
            provider_event_id=f"invalid_{uuid.uuid4().hex}",
            payload=payload,
            signature=signature,
            signature_valid=False,
            status='invalid_signature',
            error_message=f"Invalid webhook signature (claimed event id: {claimed_event_id[:100]})"
        )
        PaymentAuditLog.log_action(
            action='webhook_received',
            webhook_event=webhook_event,
            details={'error': 'Invalid webhook signature'}
        )
        return webhook_event
    
    def _apply_payment_status(self, payment_transaction: PaymentTransaction,
                              processed_data: Dict[str, any], webhook_event: WebhookEvent) -> None:
        """
        Move the transaction (and its booking) to the outcome the provider reported.

        Only transactions still pending/processing are changed, so a repeated or
        late webhook cannot flip a finished payment. A success with an amount
        that does not match the transaction is ignored and logged.
        """
        provider_status = str(processed_data.get('status') or '').lower()
        if provider_status not in PROVIDER_SUCCESS_STATUSES | PROVIDER_FAILURE_STATUSES:
            return

        with transaction.atomic():
            tx = PaymentTransaction.objects.select_for_update().get(pk=payment_transaction.pk)
            if tx.status not in ('pending', 'processing'):
                return
            old_status = tx.status

            if provider_status in PROVIDER_FAILURE_STATUSES:
                tx.status = 'failed'
                tx.error_code = 'PROVIDER_FAILED'
                tx.error_message = f'Provider reported status: {provider_status}'
                tx.save()
                PaymentAuditLog.log_action(
                    action='payment_failed', payment_transaction=tx, booking=tx.booking,
                    webhook_event=webhook_event, old_status=old_status, new_status='failed',
                    details={'provider_status': provider_status}
                )
                return

            if not self._amount_matches(processed_data.get('amount'), tx.amount):
                logger.error(
                    f"Webhook amount {processed_data.get('amount')!r} does not match "
                    f"transaction {tx.pk} amount {tx.amount}; not confirming"
                )
                webhook_event.error_message = 'Amount mismatch; payment not applied'
                return

            # The provider captured the money, so the transaction is completed
            # even if the booking can no longer be confirmed (e.g. it was
            # cancelled meanwhile); that case is flagged for a manual refund.
            tx.status = 'completed'
            tx.save()
            booking = Booking.objects.select_for_update().get(pk=tx.booking_id)
            details = {'provider_status': provider_status}
            try:
                with transaction.atomic():
                    booking.confirm_booking()
            except DjangoValidationError as e:
                logger.error(f"Paid transaction {tx.pk} but booking {booking.pk} could not be confirmed: {e}")
                details['error'] = 'Booking could not be confirmed; manual refund required'
            PaymentAuditLog.log_action(
                action='payment_completed', payment_transaction=tx, booking=booking,
                webhook_event=webhook_event, old_status=old_status, new_status='completed',
                details=details
            )

    @staticmethod
    def _amount_matches(reported_amount, expected: Decimal) -> bool:
        try:
            return Decimal(str(reported_amount)) == expected
        except (InvalidOperation, TypeError, ValueError):
            return False

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