"""
Monthly ad renewal (plan .ai/PLAN_AD_RENEWAL.md). Views and the daily task only call this module.

On an ad's end day the question "did the hotel pay for the next month?" is opened. The owner is told on that
day and again on day 3. The ad stays visible until the deadline (end day + GRACE_DAYS). The super admin answers:
  confirm  the same ad's end date moves one month on
  decline  the ad is removed now
No answer by the deadline removes the ad too. The hotel itself is never touched.
"""
import calendar
import logging
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from accounts import notify
from common.dates import business_today
from promotions import service
from promotions.models import AdRenewal, Promotion
from promotions.service import PromotionError

logger = logging.getLogger(__name__)

GRACE_DAYS = 5
REMINDER_DAYS = (0, 3)
REMINDER_CODES = ('ad_ending', 'ad_last_warning')
# Only a paid ad that is running or about to run can be renewed; paused, ended and cancelled ones are not asked about
ASKED_STATUSES = (Promotion.STATUS_SCHEDULED, Promotion.STATUS_ACTIVE)


class RenewalError(Exception):
    """A rule was broken. `code` is a stable name the API returns; `message` is for people."""

    def __init__(self, code, message=''):
        super().__init__(message or code)
        self.code = code
        self.message = message or code


def next_month_end(end: date) -> date:
    """One month on: the last day of the next month if `end` is a month's last day, else the same day (clamped)."""
    year, month = (end.year + 1, 1) if end.month == 12 else (end.year, end.month + 1)
    last_day = calendar.monthrange(year, month)[1]
    ends_the_month = end.day == calendar.monthrange(end.year, end.month)[1]
    return date(year, month, last_day if ends_the_month else min(end.day, last_day))


def open_due(today):
    """Ask about every paid, running ad whose end day has come; one question per ad and end date."""
    due = Promotion.objects.filter(
        is_deleted=False, status__in=ASKED_STATUSES, paid_at__isnull=False, end_date__lte=today)
    return sum(1 for promotion in due if AdRenewal.objects.get_or_create(
        promotion=promotion, ends_on=promotion.end_date,
        defaults={'deadline': promotion.end_date + timedelta(days=GRACE_DAYS)})[1])


def _notice_params(renewal, code):
    promotion = renewal.promotion
    params = {'promotion_id': promotion.id, 'property_id': promotion.property_id}
    if code in REMINDER_CODES:
        params.update(end_date=renewal.ends_on, until_date=renewal.deadline)
    elif code == 'ad_renewed':
        params.update(end_date=promotion.end_date)
    return params


def _tell_owner(renewal, code):
    """A notice never blocks a decision or the daily run; the caller learns whether it was stored."""
    try:
        notify(renewal.promotion.property.owner, code, _notice_params(renewal, code))
    except Exception:
        logger.exception('Ad notice %s for renewal %s was not stored', code, renewal.pk)
        return False
    return True


def send_reminders(today):
    """The latest reminder an open question has reached (day 0 or 3), once; a missed day does not send old ones."""
    sent = 0
    pending = (AdRenewal.objects.filter(status=AdRenewal.STATUS_PENDING, reminder_stage__lt=len(REMINDER_CODES))
               .select_related('promotion__property__owner'))
    for renewal in pending:
        stage = sum(1 for day in REMINDER_DAYS if (today - renewal.ends_on).days >= day)
        if stage > renewal.reminder_stage and _tell_owner(renewal, REMINDER_CODES[stage - 1]):
            renewal.reminder_stage = stage
            renewal.save(update_fields=['reminder_stage'])
            sent += 1
    return sent


def _close(renewal, status, via, actor=None):
    renewal.status = status
    renewal.decided_via = via
    renewal.decided_by = actor
    renewal.decided_at = timezone.now()
    renewal.save(update_fields=['status', 'decided_via', 'decided_by', 'decided_at'])


def _remove_ad(promotion, reason):
    """Cancel the ad without an audit row (nobody acted); the renewal row records how it ended."""
    promotion.status = Promotion.STATUS_CANCELLED
    promotion.cancelled_reason = reason
    promotion.save(update_fields=['status', 'cancelled_reason', 'updated_at'])


def expire_overdue(today):
    """No answer by the deadline: the ad is removed from the banner, the owner is told."""
    expired = 0
    overdue = (AdRenewal.objects.filter(status=AdRenewal.STATUS_PENDING, deadline__lt=today)
               .select_related('promotion__property__owner'))
    for renewal in overdue:
        with transaction.atomic():
            renewal = AdRenewal.objects.select_for_update().select_related(
                'promotion__property__owner').get(pk=renewal.pk)
            if renewal.status != AdRenewal.STATUS_PENDING:
                continue
            was_running = renewal.promotion.status in ASKED_STATUSES
            if was_running:
                _remove_ad(renewal.promotion, 'Not renewed in time')
            _close(renewal, AdRenewal.STATUS_EXPIRED, AdRenewal.VIA_AUTO)
        if was_running:
            _tell_owner(renewal, 'ad_removed')
        expired += 1
    return expired


def _decidable(renewal):
    """Re-read the renewal and its ad under a lock; refuse when somebody already answered."""
    renewal = AdRenewal.objects.select_for_update().select_related(
        'promotion__property__owner').get(pk=renewal.pk)
    if renewal.status != AdRenewal.STATUS_PENDING:
        raise RenewalError('already_decided', _('This question is already answered.'))
    return renewal


def confirm(renewal, *, actor, via=AdRenewal.VIA_PANEL):
    """The hotel paid for the next month: the same ad's end date moves one month on."""
    with transaction.atomic():
        renewal = _decidable(renewal)
        promotion = renewal.promotion
        if promotion.status not in ASKED_STATUSES:
            raise RenewalError('bad_status', _('This ad can no longer be extended.'))
        new_end = next_month_end(promotion.end_date)
        service._lock_property(promotion.property_id)
        try:
            service._check_overlap(promotion.property_id, promotion.start_date, new_end, exclude_pk=promotion.pk)
        except PromotionError:
            raise RenewalError('overlap', _('This hotel has another ad in the next month, so this one cannot be extended.'))
        promotion.end_date = new_end
        promotion.status = Promotion.STATUS_ACTIVE
        promotion.save(update_fields=['end_date', 'status', 'updated_at'])
        _close(renewal, AdRenewal.STATUS_RENEWED, via, actor)
        service._audit(actor, 'ad_renewal_confirm', promotion)
    _tell_owner(renewal, 'ad_renewed')
    return renewal


def decline(renewal, *, actor, via=AdRenewal.VIA_PANEL):
    """The hotel did not pay: the ad is removed from the banner now."""
    with transaction.atomic():
        renewal = _decidable(renewal)
        if renewal.promotion.status in ASKED_STATUSES:
            _remove_ad(renewal.promotion, 'Not renewed')
        _close(renewal, AdRenewal.STATUS_DECLINED, via, actor)
        service._audit(actor, 'ad_renewal_decline', renewal.promotion)
    _tell_owner(renewal, 'ad_removed')
    return renewal


def run_daily(today=None):
    """Open the questions, remove what is overdue, then remind the owners of what is still open."""
    today = today or business_today()
    return {'opened': open_due(today), 'expired': expire_overdue(today), 'notices': send_reminders(today)}
