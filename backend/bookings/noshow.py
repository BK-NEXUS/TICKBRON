"""
No-show esabatları (R12 3-basqısh, .ai/PLAN_R12.md 3-bólim). Mehmann mehmanxanada naqd tóleydi, sol sebepli
no-show hesh qanday pulǵa tiymeydi.

Mehmanxana mehmannıń kelmegenin xabarlaydı; staff sheshedi. Iyeler hesh qashan sheshpeydi.

create_report()    iye: bir bronǵa bir ashıq esabat, shıǵıwdan keyingi oyna ishinde
withdraw_report()  iye: tek óziniń kútip turǵan esabatın
approve_report()   staff: BIR transaction: bron -> no_show, keleshektegi túnler bosatıladı, audit qatarı,
                   bildiriwler
reject_report()    staff: bron tiyilmeydi
reverse_report()   staff túzetiwi: approved -> rejected (bron tiklenedi),
                   rejected -> approved (ádettegi tastıyıqlawdı isleydi)
flagged_property_ids()  esabat dárejesi sheklenbegen joqarı bolǵan mehmanxanalar (shegaralar sazlamalarda)
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
    """Bolıwı múmkin bolmaǵan qádem. `code` API juwapları hám testler ushın turaqlı."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


# --- inventory -----------------------------------------------------------------------------

def _future_inventory_rows(booking, today):
    """(element, `today` ten keyingi túnler ushın qulıplanǵan RoomInventory qatarları), túnler sana tártibinde."""
    from properties.models import RoomInventory

    result = []
    for item in booking.booking_items.all():
        rows = list(RoomInventory.objects.select_for_update().filter(
            room_type=item.room_type, date__gte=booking.check_in, date__lt=booking.check_out, date__gt=today,
        ).order_by('date'))
        result.append((item, rows))
    return result


def release_future_nights(booking, today):
    """Mehmann kelmeydi: búgennen keyingi túnler qayta satıwǵa shıǵadı (cancel_booking penen birdey qulıplaw)."""
    for item, rows in _future_inventory_rows(booking, today):
        for row in rows:
            row.booked_rooms = max(0, row.booked_rooms - item.number_of_rooms)
            row.save(update_fields=['booked_rooms'])


def reserve_future_nights(booking, today):
    """Biykar etilgen tastıyıqlaw ushın release_future_nights di qaytarıw; túnniń qayta satılǵanı bolsa qabıllamaydı."""
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


# --- iye: esabat beriw hám qaytarıp alıw ---------------------------------------------------

def report_deadline(booking):
    """Iye usı bronnıń haqqında esabat bere alatuǵın sońǵı is kúni."""
    return booking.check_out + timedelta(days=settings.NO_SHOW_REPORT_WINDOW_DAYS)


def reportable_bookings(queryset, today):
    """Iye búgin esabat bere alatuǵın bronlar: create_report ushın birdey qaǵıydalar, tek qulıp joq."""
    window = timedelta(days=settings.NO_SHOW_REPORT_WINDOW_DAYS)
    return queryset.filter(
        status__in=REPORTABLE_STATUSES, check_in__lt=today, check_out__gte=today - window,
    ).filter(~Exists(NoShowReport.objects.filter(booking=OuterRef('pk')).exclude(status='withdrawn')))


def create_report(booking_id, owner, comment):
    """Iye mehmannıń kelmegenin xabarlaydı. NoShowError kóteredi; NoShowReport qaytaradı."""
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


# --- staff: qararlar ---------------------------------------------------------------------

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
        return                                         # túzetilgen qarar xabarlandırıwdı hesh qashan qaytalamaydı
    notify(booking.guest, 'no_show_marked_no_refund',
           {'booking_id': booking.pk, 'booking_reference': booking.confirmation_code}, booking=booking)


def _apply_approval(report):
    """Shaqırıwshınıń transaction ı ishinde: bron -> no_show hám keleshektegi túnler bosatıladı."""
    booking = Booking.objects.select_for_update().get(pk=report.booking_id)
    try:
        booking.mark_no_show(via_approved_report=True)
    except ValidationError:
        raise NoShowError('booking_not_reportable', 'The booking can no longer be marked as a no-show')
    release_future_nights(booking, business_today())
    return booking


def approve_report(report_id, actor, decision_comment):
    """Kútip turǵan esabattı tastıyıqlaw. Esabattı qaytaradı. NoShowError kóteredi."""
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
    Qararǵa túzetiw kirgiziw. approved -> rejected: bron completed ke (shıǵıw
    ótti) yamasa confirmed ke qaytadı hám keleshektegi túnler bos bolsa qayta rezervlenedi.
    rejected -> approved: ádettegi tastıyıqlaw.
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


# --- qıylı paydalanıwdıń belgisi ---------------------------------------------------------

def flagged_property_ids(property_ids=None):
    """
    Sońǵı NO_SHOW_FLAG_DAYS kúnde qalǵanlarǵa qaraǵanda keskin kóbirek no-show xabarlaǵan mehmanxanalar:
    dáreje = jaratılǵan (qaytarıp alınbaǵan) esabatlar / kirgen bronlar (confirmed, completed, no_show).
    esabatlar >= NO_SHOW_FLAG_MIN_REPORTS HÁM dáreje >= NO_SHOW_FLAG_FACTOR x platforma
    dárejesi HÁM dáreje >= NO_SHOW_FLAG_MIN_RATE bolsa belgilenedi. Mehmanxana qansha bolsa da eki toparlanǵan query.
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
        rate = Decimal(count) / Decimal(total) if total else None      # None: bronsız esabatlar
        if rate is None or (rate >= factor * average and rate >= floor):
            flagged.add(property_id)
    return flagged
