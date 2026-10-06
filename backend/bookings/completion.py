"""
Automatic completion of finished stays (R12).

A confirmed booking whose check-out date is before the business date
(common.dates.business_today, Asia/Tashkent) becomes `completed`. The selection is
"check_out < today", not "== yesterday", so a missed run heals itself. Bookings with a pending
no-show report are skipped (staff decide first; once it is rejected or withdrawn the next run
completes it). Each booking
goes through Booking.complete_booking() in its own transaction (row lock, state
machine, PaymentAuditLog), so one failure does not undo the others. Nothing else is
touched: pending, cancelled, completed and no_show rows are never selected.

Run by the Celery beat entry `complete-finished-stays` (00:05 Asia/Tashkent) and by
`python manage.py complete_finished_stays [--dry-run]`.
"""
import logging

from django.utils import timezone

from bookings.models import AutoCompletionRun, Booking
from common.dates import business_today

logger = logging.getLogger(__name__)


class CompletionError(Exception):
    """Raised by the task after a run in which some bookings could not be completed."""


def finished_stays(today=None):
    """Confirmed bookings whose check-out date has passed (oldest check-out first)."""
    today = today or business_today()
    return (Booking.objects.filter(status='confirmed', check_out__lt=today)
            .exclude(no_show_reports__status='pending').order_by('check_out', 'pk'))


def complete_finished_stays(dry_run=False, trigger='command'):
    """Complete every finished stay. Returns {'eligible', 'changed', 'failed'}; records real runs."""
    started_at = timezone.now()
    ids = list(finished_stays().values_list('pk', flat=True))
    result = {'eligible': len(ids), 'changed': 0, 'failed': 0}
    if dry_run:
        return result
    for booking in Booking.objects.filter(pk__in=ids).order_by('check_out', 'pk'):
        try:
            booking.complete_booking()
            result['changed'] += 1
        except Exception:
            # Cancelled, completed or reported by another request after the list was made,
            # or a database error: logged with the id only, the rest still run
            if Booking.objects.filter(pk=booking.pk).exclude(status='confirmed').exists():
                continue
            logger.exception('Auto-completion failed for booking %s', booking.pk)
            result['failed'] += 1
    AutoCompletionRun.objects.create(
        trigger=trigger, started_at=started_at, finished_at=timezone.now(),
        changed=result['changed'], failed=result['failed'],
    )
    return result
