"""
Arrival of a guest who pays cash at the hotel (plan .ai/PLAN_CASH_ONLY.md stage 2).

The guest names the time they will arrive on the check-in day. The hotel marks "guest arrived"
(mark_arrived). A confirmed booking with no arrival mark ARRIVAL_GRACE_HOURS after that time is cancelled
and its rooms are released (cancel_unarrived_bookings). All times are business time (Asia/Tashkent).
Bookings made before this existed have no arrival time and are never cancelled here.
"""
import logging
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

from accounts.notifications import notify
from bookings.models import Booking
from common.dates import business_time_zone, business_today

logger = logging.getLogger(__name__)


class ArrivalCancellationError(Exception):
    """Raised after a run in which one or more unarrived bookings could not be cancelled."""


def arrival_deadline(booking):
    """Moment after which the guest counts as not arrived, or None when no arrival time was given."""
    if booking.expected_arrival_time is None:
        return None
    start = datetime.combine(booking.check_in, booking.expected_arrival_time, tzinfo=business_time_zone())
    return start + timedelta(hours=settings.ARRIVAL_GRACE_HOURS)


def arrival_time_error(check_in: date, arrival: time, now=None):
    """A message when the guest arrives today at a time that has already passed, else None."""
    now = (now or timezone.now()).astimezone(business_time_zone())
    if check_in == now.date() and arrival <= now.time().replace(tzinfo=None):
        return 'The arrival time has already passed today.'
    return None


def mark_arrived(booking, now=None):
    """The hotel says the guest arrived. Idempotent: the first time stays. ValueError says why it cannot be done."""
    if booking.status != 'confirmed':
        raise ValueError('Only a confirmed booking can be marked as arrived.')
    if booking.check_in > business_today():
        raise ValueError('The guest cannot arrive before the check-in date.')
    if booking.arrived_at is None:
        booking.arrived_at = now or timezone.now()
        booking.save(update_fields=['arrived_at', 'updated_at'])
    return booking


def _tell(booking):
    params = {'booking_id': booking.id, 'booking_reference': booking.confirmation_code}
    notify(booking.guest, 'booking_not_arrived', params, booking=booking)
    notify(booking.property.owner, 'guest_not_arrived', params, booking=booking)


def cancel_unarrived_bookings(now=None):
    """Cancel every confirmed booking past its arrival deadline. Returns {'cancelled': n, 'failed': n}."""
    now = now or timezone.now()
    candidates = (
        Booking.objects.filter(status='confirmed', arrived_at__isnull=True, expected_arrival_time__isnull=False,
                               is_deleted=False, check_in__lte=now.astimezone(business_time_zone()).date())
        .select_related('guest', 'property__owner')
    )
    cancelled = failed = 0
    for booking in candidates:
        deadline = arrival_deadline(booking)
        if deadline is None or deadline > now:
            continue
        try:
            booking.cancel_booking('no_arrival')
            _tell(booking)
            cancelled += 1
        except Exception:
            failed += 1
            logger.exception('Could not cancel the unarrived booking %s', booking.pk)
    return {'cancelled': cancelled, 'failed': failed}
