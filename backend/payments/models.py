"""
TICKBRON ushın tólem model leri.

Bul modul tólem ledgeri, adapterler hám webhook islewdiń model lerin óz ishine aladı,
idempotency, signature tekseriwi hám replay qorǵanısı menen.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from common.models import BaseModel


class PaymentTransaction(BaseModel):
    """
    TICKBRON tólem ledgeri ushın tiykarǵı Payment Transaction modeli.

    Idempotency qollawı bar tólem transaction ın kórsetedi.
    Qáwipsiz karta maǵlıwmatı hesh qashan saqlanbaydı - tek tólem provayderlerinen token lar/siltemeler.
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

    # Idempotency kilti - qaytalanǵan tólem sorawlarınıń qáwipsiz islenwin támiyinleydi
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_('Unique key for idempotent payment requests')
    )

    # Baylanıslı bron
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.PROTECT,
        related_name='payment_transactions',
        db_index=True,
        help_text=_('Associated booking for this payment')
    )

    # Tólem provayderi maǵlıwmatı
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

    # Summa maǵlıwmatı
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

    # Tólem statusı
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    # Tólem usılı token ı (hesh qashan xom karta maǵlıwmatı emes)
    payment_method_token = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_('Tokenized payment method from provider')
    )

    # Provayderdiń juwap maǵlıwmatı (tazalanǵan, jasırın maǵlıwmatsız)
    provider_response = models.JSONField(
        null=True,
        blank=True,
        help_text=_('Sanitized response data from payment provider')
    )

    # Qátelik maǵlıwmatı
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

    # Audit ushın metadata
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
        """Tólem transaction maǵlıwmatın tekseriw."""
        super().clean()

        # Jańa tólemler ushın bronnıń pending statusında ekenin tekseriw
        if self.status == 'pending' and self.booking.status != 'pending':
            raise ValidationError({
                'booking': _('Payment can only be initiated for pending bookings')
            })

        # Tólem bronnıń alınatuǵın summa snapshot ı (R6): onıń UZS summası, yamasa
        # R6 dan aldın jasalǵan bronlar ushın óz valyutasındaǵı jámi
        if self.amount != self.booking.charge_amount:
            raise ValidationError({
                'amount': _('Payment amount must match the booking charge amount')
            })
        if self.currency != self.booking.charge_currency:
            raise ValidationError({
                'currency': _('Payment currency must match the booking charge currency')
            })

    def save(self, *args, **kwargs):
        """Idempotency di májbúrlew ushın save di qayta anıqlaw."""
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_or_create_idempotent(cls, idempotency_key, **kwargs):
        """
        Bar transaction dı idempotency kilti boyınsha alıw yamasa jańa jaratıw.

        Bul qaytalanǵan tólem sorawlarınıń birdey transaction qaytarıwın,
        qos alıwdıń aldın alıwın támiyinleydi.

        Argumentler:
            idempotency_key: Idempotent soraw ushın unikal kilt
            **kwargs: Tólem transaction ınıń basqa maydanları

        Qaytaradı:
            tuple: (transaction, created), jańa transaction jaratılsa created True
        """
        try:
            transaction = cls.objects.get(idempotency_key=idempotency_key)
            return transaction, False
        except cls.DoesNotExist:
            transaction = cls.objects.create(idempotency_key=idempotency_key, **kwargs)
            return transaction, True


class Refund(models.Model):
    """
    Bir tólemniń bir qaytarıwı (R12). Qaytarıwlar ushın pul ledgeri: statistika, shekler
    hám staff dıń dıqqat talap etetuǵın dizimi usı qatarlardı oqıydı, audit tolıq maǵlıwmatındaǵı tekstti hesh qashan.

    - amount tólemniń valyutasında (UZS: pútin som); tólemniń sátsiz bolmaǵan
      qaytarıwlarınıń (pending, succeeded, needs_manual) jıyındısı onıń summasınan hesh qashan aspaydı,
      tólem qatarı qulıbı astında tekseriledi
    - pending: tastıyıqlanǵan, provayder ele shaqırılmaǵan; succeeded / failed: provayder juwabı;
      needs_manual: provayder API arqalı bunı islep almaydı (bólekleyin qaytarıw
      qollanılmaydı yamasa tekserilmegen, integraciya joq), staff qolda qaytaradı hám islendi dep belgileydi
    - idempotency_key unikal: birdey qaytarıw soraw hesh qashan ekinshi qatar jaratpaydı
    - qatarlar hesh qashan óshirilmeydi
    """
    REASON_CHOICES = [('cancel', 'Booking cancelled'), ('no_show', 'No-show'), ('staff', 'Staff decision')]
    STATUS_CHOICES = [
        ('pending', 'Pending'), ('succeeded', 'Succeeded'), ('failed', 'Failed'), ('needs_manual', 'Needs manual refund'),
    ]
    COUNTED_STATUSES = ('pending', 'succeeded', 'needs_manual')

    payment = models.ForeignKey(PaymentTransaction, on_delete=models.PROTECT, related_name='refunds')
    booking = models.ForeignKey('bookings.Booking', on_delete=models.PROTECT, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3)
    reason = models.CharField(max_length=10, choices=REASON_CHOICES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending', db_index=True)
    idempotency_key = models.CharField(max_length=100, unique=True)
    provider_reference = models.CharField(max_length=255, null=True, blank=True)
    error_code = models.CharField(max_length=50, null=True, blank=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='refunds_created')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_refunds'
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['payment', 'status'], name='refund_payment_status_idx'),
            models.Index(fields=['booking', 'status'], name='refund_booking_status_idx'),
            models.Index(fields=['status', 'created_at'], name='refund_status_created_idx'),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='refund_amount_positive'),
        ]

    def __str__(self):
        return f'Refund {self.pk} {self.amount} {self.currency} {self.status}'

    def delete(self, *args, **kwargs):
        raise PermissionError('Refunds cannot be deleted')


class WebhookEvent(BaseModel):
    """
    Tólem provayderi webhook larin islew ushın Webhook Event modeli.

    Waqıya ID sin hám waqıt belgisin tekseriw arqalı replay qorǵanısın ámelge asıradı.
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

    # Provayder maǵlıwmatı
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        db_index=True,
        help_text=_('Payment provider sending the webhook')
    )

    # Provayderdiń waqıya ID si (replay qorǵanısı ushın)
    provider_event_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_('Event ID from payment provider')
    )

    # Webhook payload ı
    payload = models.JSONField(
        help_text=_('Raw webhook payload from provider')
    )

    # Signature tekseriwi
    signature = models.CharField(
        max_length=255,
        help_text=_('Signature from provider for verification')
    )
    signature_valid = models.BooleanField(
        default=False,
        help_text=_('Whether the signature was valid')
    )

    # Waqıt belgisin tekseriw
    timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp from webhook payload')
    )
    timestamp_valid = models.BooleanField(
        default=False,
        help_text=_('Whether the timestamp was within acceptable range')
    )

    # Islew statusı
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='received',
        db_index=True
    )

    # Baylanıslı tólem transaction ı (bar bolsa)
    payment_transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhook_events',
        help_text=_('Associated payment transaction')
    )

    # Qátelik maǵlıwmatı
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text=_('Error message if processing failed')
    )

    # Islew metadata sı
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
        # Replay hújimlerdiń aldın alıw ushın unikal constraint
        unique_together = [['provider', 'provider_event_id']]

    def __str__(self):
        return f"Webhook {self.provider_event_id} from {self.provider}"

    def is_replay_attack(self):
        """
        Bul webhook waqıyasınıń replay hújim ekenin tekseriw.

        Qaytaradı:
            bool: Bul replay hújim bolsa True (qaytalanǵan waqıya ID si)
        """
        if self.id is None:
            # Saqlanbaǵan nusqalar ushın birdey ID li qálegen waqıya barlıǵın tekseriw
            return WebhookEvent.objects.filter(
                provider=self.provider,
                provider_event_id=self.provider_event_id
            ).exists()

        return WebhookEvent.objects.filter(
            provider=self.provider,
            provider_event_id=self.provider_event_id,
            id__lt=self.id  # Házirgi nusqanı shıǵarıp taslaw
        ).exists()

    def is_timestamp_valid(self, max_age_seconds=300):
        """
        Webhook waqıt belgisiniń ruxsat etilgen aralıqta ekenin tekseriw.

        Argumentler:
            max_age_seconds: Webhook tıń eń úlken jası sekundlarda (ádetde: 5 minut)

        Qaytaradı:
            bool: Waqıt belgisi jaramlı bolsa True
        """
        if not self.timestamp:
            return False

        time_diff = timezone.now() - self.timestamp
        return abs(time_diff.total_seconds()) <= max_age_seconds


class PaymentAuditLog(BaseModel):
    """
    Barlıq tólemge baylanıslı status ózgerislerin baqlaw ushın Payment Audit Log.

    Tólem ámelleri ushın tolıq audit izin beredi.
    """
    ACTION_CHOICES = [
        ('payment_initiated', _('Payment Initiated')),
        ('payment_completed', _('Payment Completed')),
        ('payment_failed', _('Payment Failed')),
        ('payment_refunded', _('Payment Refunded')),
        ('webhook_received', _('Webhook Received')),
        ('webhook_processed', _('Webhook Processed')),
        ('booking_status_changed', _('Booking Status Changed')),
        ('payment_status_changed', _('Payment Status Changed')),
    ]

    # Baylanıslı obyektler
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

    # Háreket maǵlıwmatı
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text=_('Action that was performed')
    )

    # Status ózgerisleri
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

    # Qosımsha kontekst
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
        Tólem háreketi ushın audit log jazbasın jaratıw.

        Argumentler:
            action: Orınlanǵan háreket
            payment_transaction: Baylanıslı tólem transaction ı (ıqtıyarıy)
            webhook_event: Baylanıslı webhook waqıyası (ıqtıyarıy)
            booking: Baylanıslı bron (ıqtıyarıy)
            old_status: Aldınǵı status (ıqtıyarıy)
            new_status: Jańa status (ıqtıyarıy)
            actor: Háreketti orınlaǵan paydalanıwshı (ıqtıyarıy)
            ip_address: IP mánzil (ıqtıyarıy)
            details: Qosımsha tolıq maǵlıwmat (ıqtıyarıy)

        Qaytaradı:
            PaymentAuditLog: Jaratılǵan audit log jazbası
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
