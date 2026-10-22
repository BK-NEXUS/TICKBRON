"""
No-show reports (R12 phase 3, .ai/PLAN_R12.md section 3). The guest pays cash at the hotel, so a
no-show moves no money.

The hotel reports that a guest did not arrive; staff decide. Owners never decide.

create_report()    owner: one open report per booking, inside the window after check-out
withdraw_report()  owner: own pending report only
approve_report()   staff: ONE transaction: booking -> no_show, future nights released, audit row,
                   notifications
reject_report()    staff: the booking is untouched
reverse_report()   staff correction: approved -> rejected (the booking is restored),
                   rejected -> approved (runs the normal approval)
flagged_property_ids()  hotels whose report rate is unusually high (thresholds are settings)
"""
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Exists, OuterRef
from django.utils import timezone

from accounts.models import Notification
from accounts.notifications import notify
from admin_panel.models import AdminAccessLog
from bookings.models import Booking, NoShowReport
from common.dates import business_today

REPORTABLE_STATUSES = ('confirmed', 'completed')


class NoShowError(Exception):
    """A step that may not happen. `code` is stable for API responses and tests."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


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

def report_deadline(booking):
    """Last business day on which the owner may still report this booking."""
    return booking.check_out + timedelta(days=settings.NO_SHOW_REPORT_WINDOW_DAYS)


def reportable_bookings(queryset, today):
    """Bookings the owner can report today: the same rules create_report enforces, minus the lock."""
    window = timedelta(days=settings.NO_SHOW_REPORT_WINDOW_DAYS)
    return queryset.filter(
        status__in=REPORTABLE_STATUSES, check_in__lt=today, check_out__gte=today - window,
    ).filter(~Exists(NoShowReport.objects.filter(booking=OuterRef('pk')).exclude(status='withdrawn')))


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
        if today > report_deadline(booking):
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


def _notify_guest(booking):
    if Notification.objects.filter(booking=booking, code__in=('no_show_marked', 'no_show_marked_no_refund')).exists():
        return                                         # a corrected decision never repeats the notice
    notify(booking.guest, 'no_show_marked_no_refund',
           {'booking_id': booking.pk, 'booking_reference': booking.confirmation_code}, booking=booking)


def _apply_approval(report):
    """Inside the caller's transaction: booking -> no_show and the future nights released."""
    booking = Booking.objects.select_for_update().get(pk=report.booking_id)
    try:
        booking.mark_no_show(via_approved_report=True)
    except ValidationError:
        raise NoShowError('booking_not_reportable', 'The booking can no longer be marked as a no-show')
    release_future_nights(booking, business_today())
    return booking


def approve_report(report_id, actor, decision_comment):
    """Approve a pending report. Returns the report. Raises NoShowError."""
    with transaction.atomic():
        report = _lock_report(report_id)
        if report.status != 'pending':
            raise NoShowError('not_pending', 'Only a pending report can be decided')
        return _approve_locked(report, actor, decision_comment)


def _approve_locked(report, actor, decision_comment, audit=True):
    booking = _apply_approval(report)
    _decide(report, 'approved', actor, decision_comment)
    if audit:
        _audit(actor, 'no_show_report_approve', report)
    _notify_owner(report, 'no_show_report_approved')
    _notify_guest(booking)
    return report


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
    passed) or confirmed and the future nights are reserved again if still free.
    rejected -> approved: the normal approval.
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
