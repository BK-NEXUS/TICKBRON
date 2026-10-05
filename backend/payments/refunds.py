"""
Refunds (R12). One place that creates, sends and settles Refund rows.

create_refund()  inside a transaction with the payment row locked: validates the amount
                 (positive, whole so'm for UZS) and that the payment's non-failed refunds
                 plus this one never exceed what was paid; stores the row as `pending`, or
                 `needs_manual` when the provider cannot refund this amount through its API.
send_refund()    AFTER the row is committed and outside any transaction: calls the provider
                 once, then records succeeded / failed and moves the payment and booking
                 payment status. Never called for needs_manual rows.
mark_manual_done(), retry_refund()  staff follow-up from the needs-attention list.
"""
import logging
import uuid
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Sum

from common.money import CHARGE_CURRENCY, is_whole_som
from payments.adapters import PaymentAdapterError, get_payment_adapter
from payments.models import PaymentAuditLog, PaymentTransaction, Refund

logger = logging.getLogger(__name__)

REFUNDABLE_PAYMENT_STATUSES = ('completed', 'partially_refunded')


class RefundError(ValueError):
    """A refund that may not be created. `code` is stable for API responses and tests."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def _sum(payment, statuses):
    total = Refund.objects.filter(payment=payment, status__in=statuses).aggregate(total=Sum('amount'))['total']
    return total or Decimal('0')


def remaining_amount(payment):
    """What can still be refunded: paid minus every refund that is not failed."""
    return payment.amount - _sum(payment, Refund.COUNTED_STATUSES)


def _parse_amount(amount, currency):
    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        raise RefundError('invalid_amount', 'Refund amount must be a number')
    if not amount.is_finite() or amount <= 0:
        raise RefundError('invalid_amount', 'Refund amount must be greater than zero')
    if currency == CHARGE_CURRENCY and not is_whole_som(amount):
        raise RefundError('not_whole_som', "UZS refunds must be whole so'm")
    return amount


def create_refund(payment, amount, reason, created_by=None, idempotency_key=None):
    """
    Store a refund of `amount` of `payment` (locks the payment row). Returns the Refund.

    The same idempotency_key returns the existing row unchanged. Raises RefundError.
    """
    with transaction.atomic():
        payment = PaymentTransaction.objects.select_for_update().get(pk=payment.pk)
        if idempotency_key:
            existing = Refund.objects.filter(idempotency_key=idempotency_key).first()
            if existing is not None:
                return existing
        if payment.status not in REFUNDABLE_PAYMENT_STATUSES:
            raise RefundError('payment_not_refundable', 'Only completed payments can be refunded')
        amount = _parse_amount(amount, payment.currency)
        if amount > remaining_amount(payment):
            raise RefundError('limit_exceeded', 'Refund amount cannot exceed the payment amount')

        is_partial = amount < payment.amount
        status = 'pending'
        if is_partial and not get_payment_adapter(payment.provider).partial_refund_supported():
            status = 'needs_manual'
        try:
            with transaction.atomic():
                return Refund.objects.create(
                    payment=payment, booking_id=payment.booking_id, amount=amount, currency=payment.currency,
                    reason=reason, status=status, created_by=created_by,
                    idempotency_key=idempotency_key or f'refund:{uuid.uuid4().hex}',
                )
        except IntegrityError:
            if idempotency_key:
                return Refund.objects.get(idempotency_key=idempotency_key)
            raise


def _settle_payment(payment, actor=None):
    """Payment and booking payment status follow the succeeded refunds (payment row locked)."""
    refunded = _sum(payment, ('succeeded',))
    if refunded <= 0:
        return
    new_status = 'refunded' if refunded >= payment.amount else 'partially_refunded'
    if payment.status == new_status:
        return
    payment.status = new_status
    payment.save()
    from bookings.models import Booking
    booking = Booking.objects.get(pk=payment.booking_id)
    try:
        with transaction.atomic():
            booking.update_payment_status(new_status)
    except DjangoValidationError:
        # A booking never marked paid (payment captured after it was cancelled) keeps its
        # payment status; the refund itself still stands
        pass


def send_refund(refund, actor=None, ip_address=None, extra_details=None):
    """
    Ask the provider for a `pending` refund (once) and record the answer. Must run after the
    refund row is committed, outside any transaction. Returns the refreshed Refund.
    """
    with transaction.atomic():
        refund = Refund.objects.select_for_update().get(pk=refund.pk)
        if refund.status != 'pending':
            return refund
        payment = PaymentTransaction.objects.get(pk=refund.payment_id)

    adapter = get_payment_adapter(payment.provider)
    error_code = None
    response = None
    try:
        response = adapter.refund_payment(
            provider_transaction_id=payment.provider_transaction_id, amount=refund.amount,
            refund_reference=refund.idempotency_key,
        )
    except NotImplementedError:
        error_code = 'PROVIDER_NOT_INTEGRATED'
    except PaymentAdapterError:
        logger.warning('Refund %s failed at the provider', refund.pk)
        error_code = 'REFUND_ERROR'

    with transaction.atomic():
        payment = PaymentTransaction.objects.select_for_update().get(pk=refund.payment_id)
        refund = Refund.objects.select_for_update().get(pk=refund.pk)
        if refund.status != 'pending':
            return refund
        old_payment_status = payment.status
        if error_code == 'PROVIDER_NOT_INTEGRATED':
            refund.status, refund.error_code = 'needs_manual', error_code
        elif error_code:
            refund.status, refund.error_code = 'failed', error_code
            payment.error_code = 'REFUND_ERROR'
            payment.error_message = 'Refund failed at the provider'
            payment.save()
        else:
            refund.status = 'succeeded'
            refund.error_code = None
            reference = (response or {}).get('refund_id') or (response or {}).get('id')
            refund.provider_reference = str(reference) if reference else f'{payment.provider}:{refund.idempotency_key}'
        refund.save()
        if refund.status == 'succeeded':
            _settle_payment(payment, actor)
        PaymentAuditLog.log_action(
            action='payment_refunded' if refund.status == 'succeeded' else 'payment_failed',
            payment_transaction=payment, booking=payment.booking, old_status=old_payment_status,
            new_status=payment.status, actor=actor, ip_address=ip_address,
            details={'refund_id': refund.id, 'refund_amount': str(refund.amount), 'reason': refund.reason,
                     'refund_status': refund.status, 'provider_response': response, **(extra_details or {})},
        )
    return refund


def mark_manual_done(refund, provider_reference, actor):
    """Staff refunded a needs_manual refund by hand (bank / provider cabinet)."""
    with transaction.atomic():
        refund = Refund.objects.select_for_update().get(pk=refund.pk)
        if refund.status != 'needs_manual':
            raise RefundError('not_manual', 'Only refunds waiting for a manual refund can be marked done')
        payment = PaymentTransaction.objects.select_for_update().get(pk=refund.payment_id)
        old_payment_status = payment.status
        refund.status = 'succeeded'
        refund.provider_reference = provider_reference
        refund.save()
        _settle_payment(payment, actor)
        PaymentAuditLog.log_action(
            action='payment_refunded', payment_transaction=payment, booking=payment.booking,
            old_status=old_payment_status, new_status=payment.status, actor=actor,
            details={'refund_id': refund.id, 'refund_amount': str(refund.amount), 'reason': refund.reason,
                     'refund_status': 'succeeded', 'manual': True},
        )
    return refund


def retry_refund(refund, actor):
    """Send a failed refund again (same row, same idempotency key, provider asked once more)."""
    with transaction.atomic():
        refund = Refund.objects.select_for_update().get(pk=refund.pk)
        if refund.status != 'failed':
            raise RefundError('not_failed', 'Only failed refunds can be retried')
        payment = PaymentTransaction.objects.select_for_update().get(pk=refund.payment_id)
        if refund.amount > remaining_amount(payment):
            raise RefundError('limit_exceeded', 'Refund amount cannot exceed the payment amount')
        refund.status = 'pending'
        refund.error_code = None
        refund.save()
    return send_refund(refund, actor=actor)
