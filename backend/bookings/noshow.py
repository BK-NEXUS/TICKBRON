"""
No-show reports and the no-show refund (R12 phase 3, .ai/PLAN_R12.md sections 3 and 4).

The hotel reports that a guest did not arrive; staff decide. Owners never decide.

create_report()    owner: one open report per booking, inside the window after check-out
withdraw_report()  owner: own pending report only
approve_report()   staff: ONE transaction: booking -> no_show, future nights released, Refund rows
                   (idempotency key "<booking id>:no_show"), audit row, notifications. The provider
                   is called AFTER commit through payments.refunds.send_refund.
reject_report()    staff: the booking is untouched, no money moves
reverse_report()   staff correction: approved -> rejected (money already refunded is NOT taken back),
                   rejected -> approved (runs the normal approval; the refund exists once)
flagged_property_ids()  hotels whose report rate is unusually high (thresholds are settings)
refund_previews()  the exact refund an approval would pay, computed with the same functions
"""
import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from functools import partial

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Sum
from django.utils import timezone

from accounts.models import Notification
from accounts.notifications import notify
from admin_panel.models import AdminAccessLog
from bookings.models import Booking, NoShowReport
from common.dates import business_today
from common.money import CHARGE_CURRENCY, quantize
from payments.models import PaymentTransaction, Refund
from payments.refunds import RefundError, create_refund, remaining_amount, send_refund

logger = logging.getLogger(__name__)

PAID_PAYMENT_STATUSES = ('completed', 'partially_refunded', 'refunded')
REPORTABLE_STATUSES = ('confirmed', 'completed')
TEXT_KEY = 'no_show_refund_statement'


class NoShowError(Exception):
    """A step that may not happen. `code` is stable for API responses and tests."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


# --- disclosure (quote, booking creation, booking detail) ---------------------------------

def refund_amount_for(percent, charge_amount, charge_currency=CHARGE_CURRENCY):
    """The UZS refund promised for a charge: whole so'm, ROUND_HALF_UP. None when it cannot be told."""
    if charge_amount is None or charge_currency != CHARGE_CURRENCY:
        return None
    return quantize(Decimal(charge_amount) * Decimal(percent) / Decimal(100), CHARGE_CURRENCY)


def refund_disclosure(percent, charge_amount, charge_currency=CHARGE_CURRENCY):
    """
    The fields every guest-facing response carries. The frontend renders the sentence from
    `no_show_refund_text_key` + `no_show_refund_text_params` in the guest's language and never
    computes the amount itself. Percent 0 (old bookings, or the setting at 0) promises nothing.
    """
    if not percent:
        return {'no_show_refund_percent': 0, 'no_show_refund_amount': None,
                'no_show_refund_text_key': None, 'no_show_refund_text_params': None}
    amount = refund_amount_for(percent, charge_amount, charge_currency)
    amount_text = f'{amount:.2f}' if amount is not None else None
    return {
        'no_show_refund_percent': percent,
        'no_show_refund_amount': amount_text,
        'no_show_refund_text_key': TEXT_KEY,
        'no_show_refund_text_params': {'percent': percent, 'amount': amount_text},
    }


# --- the refund an approval pays ----------------------------------------------------------

def _target(paid, percent):
    return quantize(Decimal(paid) * Decimal(percent) / Decimal(100), CHARGE_CURRENCY)


def _refund_now(paid, already, percent):
    """target = percent of what was paid; pay what is still missing, never below 0, never above paid."""
    target = min(_target(paid, percent), paid)
    return max(Decimal('0'), target - already)


def refund_previews(bookings):
    """
    {booking id: {amount, currency, percent, already_refunded, paid}} for a list of bookings in
    two queries however many there are (the staff queue). Same arithmetic as approval.
    """
    ids = [booking.pk for booking in bookings]
    paid = dict(PaymentTransaction.objects.filter(
        booking_id__in=ids, currency=CHARGE_CURRENCY, status__in=PAID_PAYMENT_STATUSES,
    ).values('booking_id').annotate(total=Sum('amount')).values_list('booking_id', 'total'))
    already = dict(Refund.objects.filter(
        booking_id__in=ids, currency=CHARGE_CURRENCY, status__in=Refund.COUNTED_STATUSES,
    ).values('booking_id').annotate(total=Sum('amount')).values_list('booking_id', 'total'))
    previews = {}
    for booking in bookings:
        booking_paid = paid.get(booking.pk) or Decimal('0')
        booking_already = already.get(booking.pk) or Decimal('0')
        percent = booking.no_show_refund_percent
        previews[booking.pk] = {
            'amount': f'{_refund_now(booking_paid, booking_already, percent):.2f}',
            'currency': CHARGE_CURRENCY,
            'percent': percent,
            'already_refunded': f'{booking_already:.2f}',
            'paid': f'{booking_paid:.2f}',
        }
    return previews


def _refund_allocations(booking):
    """
    Locks the booking's payments and returns [(payment, amount)]: the refund split across the
    payments, newest first, never more than each payment still has. Total = _refund_now().
    """
    payments = list(PaymentTransaction.objects.select_for_update().filter(
        booking=booking, currency=CHARGE_CURRENCY, status__in=PAID_PAYMENT_STATUSES,
    ).order_by('-created_at', '-id'))
    paid = sum((payment.amount for payment in payments), Decimal('0'))
    already = Refund.objects.filter(
        booking=booking, currency=CHARGE_CURRENCY, status__in=Refund.COUNTED_STATUSES,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    left = _refund_now(paid, already, booking.no_show_refund_percent)
    allocations = []
    for payment in payments:
        if left <= 0:
            break
        take = min(left, remaining_amount(payment))
        if take > 0:
            allocations.append((payment, take))
            left -= take
    return allocations


# --- inventory -----------------------------------------------------------------------------

def _future_inventory_rows(booking, today):
    """(item, locked RoomInventory rows for the nights after `today`), nights in date order."""
    from properties.models import RoomInventory

    result = []
    for item in booking.booking_items.all():
        rows = list(RoomInventory.objects.select_for_update().filter(
            room_type=item.room_type, date__gte=booking.check_in, date__lt=booking.check_out, date__gt=today,
        ).order_by('date'))
        result.append((item, rows))
    return result


def release_future_nights(booking, today):
    """The guest is not coming: nights after today go back on sale (same locking as cancel_booking)."""
    for item, rows in _future_inventory_rows(booking, today):
        for row in rows:
            row.booked_rooms = max(0, row.booked_rooms - item.number_of_rooms)
            row.save(update_fields=['booked_rooms'])


def reserve_future_nights(booking, today):
    """Undo release_future_nights for a reversed approval; refuses when a night was sold again."""
    plan = _future_inventory_rows(booking, today)
    for item, rows in plan:
        for row in rows:
            if row.remaining_rooms < item.number_of_rooms:
                raise NoShowError('inventory_unavailable',
                                  'The nights after today were sold again; the decision cannot be reversed')
    for item, rows in plan:
        for row in rows:
            row.booked_rooms += item.number_of_rooms
            row.save(update_fields=['booked_rooms'])


# --- owner: report and withdraw -----------------------------------------------------------

def create_report(booking_id, owner, comment):
    """Owner reports that the guest did not arrive. Raises NoShowError; returns the NoShowReport."""
    today = business_today()
    with transaction.atomic():
        booking = Booking.objects.select_for_update(of=('self',)).select_related('property').filter(
            pk=booking_id, is_deleted=False, property__owner=owner).first()
        if booking is None:
            raise NoShowError('not_found', 'Booking not found')
        if booking.status not in REPORTABLE_STATUSES:
            raise NoShowError('not_reportable_status', 'Only confirmed or completed bookings can be reported')
        if not booking.check_in < today:
            raise NoShowError('too_early', 'A no-show can be reported from the day after check-in')
        if today > booking.check_out + timedelta(days=settings.NO_SHOW_REPORT_WINDOW_DAYS):
            raise NoShowError('window_closed', 'The time to report this booking has passed')
        if booking.no_show_reports.exclude(status='withdrawn').exists():
            raise NoShowError('report_exists', 'This booking already has a no-show report')
        try:
            with transaction.atomic():
                return NoShowReport.objects.create(
                    booking=booking, property=booking.property, created_by=owner, comment=comment)
        except IntegrityError:
            raise NoShowError('report_exists', 'This booking already has a no-show report')


def withdraw_report(report_id, owner):
    with transaction.atomic():
        report = NoShowReport.objects.select_for_update().filter(pk=report_id, property__owner=owner).first()
        if report is None:
            raise NoShowError('not_found', 'Report not found')
        if report.status != 'pending':
            raise NoShowError('not_pending', 'Only a pending report can be withdrawn')
        report.status = 'withdrawn'
        report.save(update_fields=['status', 'updated_at'])
        return report


# --- staff: decisions ---------------------------------------------------------------------

def _lock_report(report_id):
    report = NoShowReport.objects.select_for_update().filter(pk=report_id).first()
    if report is None:
        raise NoShowError('not_found', 'Report not found')
    return report


def _decide(report, status, actor, decision_comment):
    report.status = status
    report.decided_by = actor
    report.decision_comment = decision_comment
    report.decided_at = timezone.now()
    report.save(update_fields=['status', 'decided_by', 'decision_comment', 'decided_at', 'updated_at'])


def _audit(actor, action, report):
    AdminAccessLog.record(actor, action, target_booking_id=report.booking_id, details={'report_id': report.pk})


def _notify_owner(report, code):
    notify(report.created_by or report.property.owner, code, {
        'report_id': report.pk, 'booking_id': report.booking_id,
        'booking_reference': report.booking.confirmation_code,
    }, booking=report.booking)


def _notify_guest(booking, refund_total):
    if Notification.objects.filter(booking=booking, code__in=('no_show_marked', 'no_show_marked_no_refund')).exists():
        return                                         # a corrected decision never repeats the notice
    base = {'booking_id': booking.pk, 'booking_reference': booking.confirmation_code}
    if refund_total > 0:
        notify(booking.guest, 'no_show_marked', {
            **base, 'amount': str(int(refund_total)), 'currency': CHARGE_CURRENCY,
            'percent': booking.no_show_refund_percent}, booking=booking)
    else:
        notify(booking.guest, 'no_show_marked_no_refund', base, booking=booking)


def _apply_approval(report, actor):
    """
    Inside the caller's transaction: booking -> no_show, future nights released, Refund rows.
    Returns the Refund rows created now (pending or needs_manual).
    """
    booking = Booking.objects.select_for_update().get(pk=report.booking_id)
    try:
        booking.mark_no_show(via_approved_report=True)
    except ValidationError:
        raise NoShowError('booking_not_reportable', 'The booking can no longer be marked as a no-show')
    release_future_nights(booking, business_today())
    refunds = []
    for index, (payment, amount) in enumerate(_refund_allocations(booking)):
        key = f'{booking.pk}:no_show' if index == 0 else f'{booking.pk}:no_show:{payment.pk}'
        try:
            refunds.append(create_refund(payment, amount, 'no_show', created_by=actor, idempotency_key=key))
        except RefundError as exc:                      # cannot happen with the locks held; never half-approve
            raise NoShowError('refund_refused', exc.message)
    return booking, refunds


def _send_after_commit(refunds, actor):
    ids = [refund.pk for refund in refunds if refund.status == 'pending']
    if ids:
        transaction.on_commit(partial(send_pending_no_show_refunds, ids, actor))


def send_pending_no_show_refunds(refund_ids, actor):
    """After commit, outside any transaction: ask the provider once for each pending refund."""
    for refund in Refund.objects.filter(pk__in=refund_ids):
        try:
            send_refund(refund, actor=actor)
        except Exception:                               # the decision is committed; staff see the refund
            logger.exception('No-show refund %s could not be sent', refund.pk)


def approve_report(report_id, actor, decision_comment):
    """Approve a pending report. Returns (report, refunds created now). Raises NoShowError."""
    with transaction.atomic():
        report = _lock_report(report_id)
        if report.status != 'pending':
            raise NoShowError('not_pending', 'Only a pending report can be decided')
        return _approve_locked(report, actor, decision_comment)


def _approve_locked(report, actor, decision_comment, audit=True):
    booking, refunds = _apply_approval(report, actor)
    _decide(report, 'approved', actor, decision_comment)
    if audit:
        _audit(actor, 'no_show_report_approve', report)
    _notify_owner(report, 'no_show_report_approved')
    _notify_guest(booking, sum((refund.amount for refund in refunds), Decimal('0')))
    _send_after_commit(refunds, actor)
    return report, refunds


def reject_report(report_id, actor, decision_comment):
    with transaction.atomic():
        report = _lock_report(report_id)
        if report.status != 'pending':
            raise NoShowError('not_pending', 'Only a pending report can be decided')
        _decide(report, 'rejected', actor, decision_comment)
        _audit(actor, 'no_show_report_reject', report)
        _notify_owner(report, 'no_show_report_rejected')
        return report


def reverse_report(report_id, actor, decision_comment):
    """
    Correct a decision. approved -> rejected: the booking goes back to completed (check-out
    passed) or confirmed, the future nights are reserved again if still free, and money already
    refunded stays refunded. rejected -> approved: the normal approval (the refund exists once).
    """
    with transaction.atomic():
        report = _lock_report(report_id)
        if report.status == 'rejected':
            _approve_locked(report, actor, decision_comment, audit=False)
        elif report.status == 'approved':
            booking = Booking.objects.select_for_update().get(pk=report.booking_id)
            today = business_today()
            try:
                booking.restore_after_reversed_no_show(completed=booking.check_out < today)
            except ValidationError:
                raise NoShowError('booking_not_reportable', 'The booking can no longer be restored')
            reserve_future_nights(booking, today)
            _decide(report, 'rejected', actor, decision_comment)
            _notify_owner(report, 'no_show_report_rejected')
        else:
            raise NoShowError('not_decided', 'Only an approved or rejected report can be corrected')
        _audit(actor, 'no_show_report_reverse', report)
        return report


# --- the abuse flag -----------------------------------------------------------------------

def flagged_property_ids(property_ids=None):
    """
    Hotels reporting far more no-shows than the rest, over the last NO_SHOW_FLAG_DAYS days:
    rate = reports created (not withdrawn) / bookings checked in (confirmed, completed, no_show).
    Flagged when reports >= NO_SHOW_FLAG_MIN_REPORTS AND rate >= NO_SHOW_FLAG_FACTOR x the
    platform rate AND rate >= NO_SHOW_FLAG_MIN_RATE. Two grouped queries however many hotels.
    """
    days = int(settings.NO_SHOW_FLAG_DAYS)
    reports = dict(NoShowReport.objects.filter(created_at__gte=timezone.now() - timedelta(days=days))
                   .exclude(status='withdrawn').values('property_id').annotate(n=Count('id'))
                   .values_list('property_id', 'n'))
    if not reports:
        return set()
    today = business_today()
    bookings = dict(Booking.objects.filter(
        is_deleted=False, status__in=('confirmed', 'completed', 'no_show'),
        check_in__gte=today - timedelta(days=days), check_in__lte=today,
    ).values('property_id').annotate(n=Count('id')).values_list('property_id', 'n'))
    total_reports, total_bookings = sum(reports.values()), sum(bookings.values())
    average = Decimal(total_reports) / Decimal(total_bookings) if total_bookings else Decimal('0')
    try:
        factor = Decimal(str(settings.NO_SHOW_FLAG_FACTOR))
        floor = Decimal(str(settings.NO_SHOW_FLAG_MIN_RATE))
    except InvalidOperation:
        return set()
    flagged = set()
    for property_id, count in reports.items():
        if property_ids is not None and property_id not in property_ids:
            continue
        if count < int(settings.NO_SHOW_FLAG_MIN_REPORTS):
            continue
        total = bookings.get(property_id, 0)
        rate = Decimal(count) / Decimal(total) if total else None      # None: reports without bookings
        if rate is None or (rate >= factor * average and rate >= floor):
            flagged.add(property_id)
    return flagged
