"""
Payment models for TICKBRON.

This module contains models for payment ledger, adapters, and webhook processing
with idempotency, signature validation, and replay protection.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from common.models import BaseModel
import secrets


class PaymentTransaction(BaseModel):
    """
    Core Payment Transaction model for TICKBRON payment ledger.
    
    Represents a payment transaction with idempotency support.
    Raw card data is never stored - only tokens/references from payment providers.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
        ('partially_refunded', _('Partially Refunded')),
    ]
    
    PROVIDER_CHOICES = [
        ('payme', _('Payme')),
        ('click', _('Click')),
        ('visa', _('Visa')),
    ]
    
    # Idempotency key - ensures duplicate payment requests are handled safely
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_('Unique key for idempotent payment requests')
    )
    
    # Associated booking
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.PROTECT,
        related_name='payment_transactions',
        db_index=True,
        help_text=_('Associated booking for this payment')
    )
    
    # Payment provider information
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        db_index=True,
        help_text=_('Payment provider (payme, click, visa)')
    )
    provider_transaction_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Transaction ID from payment provider')
    )
    
    # Amount information
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Payment amount')
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text=_('ISO 4217 currency code')
    )
    
    # Payment status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Payment method token (never raw card data)
    payment_method_token = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_('Tokenized payment method from provider')
    )
    
    # Response data from provider (sanitized, no sensitive data)
    provider_response = models.JSONField(
        null=True,
        blank=True,
        help_text=_('Sanitized response data from payment provider')
    )
    
    # Error information
    error_code = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_('Error code from payment provider')
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text=_('Error message from payment provider')
    )
    
    # Metadata for auditing
    client_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_('Client IP address for audit trail')
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text=_('User agent string for audit trail')
    )
    
    class Meta:
        db_table = 'payment_transactions'
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['booking', 'status']),
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['provider_transaction_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.idempotency_key} - {self.amount} {self.currency}"
    
    def clean(self):
        """Validate payment transaction data."""
        super().clean()
        
        # Validate that booking is in pending status for new payments
        if self.status == 'pending' and self.booking.status != 'pending':
            raise ValidationError({
                'booking': _('Payment can only be initiated for pending bookings')
            })
        
        # Validate amount matches booking total
        if self.amount != self.booking.total_price:
            raise ValidationError({
                'amount': _('Payment amount must match booking total')
            })
    
    def save(self, *args, **kwargs):
        """Override save to enforce idempotency."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_or_create_idempotent(cls, idempotency_key, **kwargs):
        """
        Get existing transaction by idempotency key or create new one.
        
        This ensures that duplicate payment requests return the same transaction,
        preventing duplicate charges.
        
        Args:
            idempotency_key: Unique key for idempotent request
            **kwargs: Other fields for payment transaction
        
        Returns:
            tuple: (transaction, created) where created is True if new transaction was created
        """
        try:
            transaction = cls.objects.get(idempotency_key=idempotency_key)
            return transaction, False
        except cls.DoesNotExist:
            transaction = cls.objects.create(idempotency_key=idempotency_key, **kwargs)
            return transaction, True


class WebhookEvent(BaseModel):
    """
    Webhook Event model for processing payment provider webhooks.
    
    Implements replay protection through event ID tracking and timestamp validation.
    """
    STATUS_CHOICES = [
        ('received', _('Received')),
        ('processed', _('Processed')),
        ('failed', _('Failed')),
        ('invalid_signature', _('Invalid Signature')),
        ('replay_attack', _('Replay Attack')),
    ]
    
    PROVIDER_CHOICES = [
        ('payme', _('Payme')),
        ('click', _('Click')),
        ('visa', _('Visa')),
    ]
    
    # Provider information
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        db_index=True,
        help_text=_('Payment provider sending the webhook')
    )
    
    # Event ID from provider (for replay protection)
    provider_event_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_('Event ID from payment provider')
    )
    
    # Webhook payload
    payload = models.JSONField(
        help_text=_('Raw webhook payload from provider')
    )
    
    # Signature verification
    signature = models.CharField(
        max_length=255,
        help_text=_('Signature from provider for verification')
    )
    signature_valid = models.BooleanField(
        default=False,
        help_text=_('Whether the signature was valid')
    )
    
    # Timestamp validation
    timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp from webhook payload')
    )
    timestamp_valid = models.BooleanField(
        default=False,
        help_text=_('Whether the timestamp was within acceptable range')
    )
    
    # Processing status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='received',
        db_index=True
    )
    
    # Associated payment transaction (if any)
    payment_transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhook_events',
        help_text=_('Associated payment transaction')
    )
    
    # Error information
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text=_('Error message if processing failed')
    )
    
    # Processing metadata
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the webhook was processed')
    )
    
    class Meta:
        db_table = 'webhook_events'
        verbose_name = 'Webhook Event'
        verbose_name_plural = 'Webhook Events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'provider_event_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
        # Unique constraint to prevent replay attacks
        unique_together = [['provider', 'provider_event_id']]
    
    def __str__(self):
        return f"Webhook {self.provider_event_id} from {self.provider}"
    
    def is_replay_attack(self):
        """
        Check if this webhook event is a replay attack.
        
        Returns:
            bool: True if this is a replay attack (duplicate event ID)
        """
        if self.id is None:
            # For unsaved instances, check if any event with same ID exists
            return WebhookEvent.objects.filter(
                provider=self.provider,
                provider_event_id=self.provider_event_id
            ).exists()
        
        return WebhookEvent.objects.filter(
            provider=self.provider,
            provider_event_id=self.provider_event_id,
            id__lt=self.id  # Exclude current instance
        ).exists()
    
    def is_timestamp_valid(self, max_age_seconds=300):
        """
        Check if webhook timestamp is within acceptable range.
        
        Args:
            max_age_seconds: Maximum age of webhook in seconds (default: 5 minutes)
        
        Returns:
            bool: True if timestamp is valid
        """
        if not self.timestamp:
            return False
        
        time_diff = timezone.now() - self.timestamp
        return abs(time_diff.total_seconds()) <= max_age_seconds


class PaymentAuditLog(BaseModel):
    """
    Payment Audit Log for tracking all payment-related state changes.
    
    Provides a complete audit trail for payment operations.
    """
    ACTION_CHOICES = [
        ('payment_initiated', _('Payment Initiated')),
        ('payment_completed', _('Payment Completed')),
        ('payment_failed', _('Payment Failed')),
        ('payment_refunded', _('Payment Refunded')),
        ('webhook_received', _('Webhook Received')),
        ('webhook_processed', _('Webhook Processed')),
        ('booking_status_changed', _('Booking Status Changed')),
    ]
    
    # Associated entities
    payment_transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text=_('Associated payment transaction')
    )
    webhook_event = models.ForeignKey(
        WebhookEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text=_('Associated webhook event')
    )
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_audit_logs',
        help_text=_('Associated booking')
    )
    
    # Action information
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text=_('Action that was performed')
    )
    
    # State changes
    old_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Previous status before action')
    )
    new_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_('New status after action')
    )
    
    # Additional context
    actor = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_audit_logs',
        help_text=_('User who performed the action (if applicable)')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_('IP address of the actor')
    )
    details = models.JSONField(
        null=True,
        blank=True,
        help_text=_('Additional details about the action')
    )
    
    class Meta:
        db_table = 'payment_audit_logs'
        verbose_name = 'Payment Audit Log'
        verbose_name_plural = 'Payment Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_transaction']),
            models.Index(fields=['webhook_event']),
            models.Index(fields=['booking']),
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Audit Log {self.action} at {self.created_at}"
    
    @classmethod
    def log_action(cls, action, payment_transaction=None, webhook_event=None, 
                   booking=None, old_status=None, new_status=None, actor=None, 
                   ip_address=None, details=None):
        """
        Create an audit log entry for a payment action.
        
        Args:
            action: Action that was performed
            payment_transaction: Associated payment transaction (optional)
            webhook_event: Associated webhook event (optional)
            booking: Associated booking (optional)
            old_status: Previous status (optional)
            new_status: New status (optional)
            actor: User who performed the action (optional)
            ip_address: IP address (optional)
            details: Additional details (optional)
        
        Returns:
            PaymentAuditLog: Created audit log entry
        """
        return cls.objects.create(
            payment_transaction=payment_transaction,
            webhook_event=webhook_event,
            booking=booking,
            action=action,
            old_status=old_status,
            new_status=new_status,
            actor=actor,
            ip_address=ip_address,
            details=details
        )
