"""
Mehmanxanada naqd tóleytuǵın mehmannıń keliwi (reje .ai/PLAN_CASH_ONLY.md 2-basqısh).

Mehmann kiriw kúni qaysı waqıtta keletuǵının aytadı. Mehmanxana "mehmann keldi" dep belgileydi
(mark_arrived). Sol waqıttan keyin ARRIVAL_GRACE_HOURS saat ótip, keliw belgisi joq tastıyıqlanǵan bron biykar etiledi
hám xonaları bosatıladı (cancel_unarrived_bookings). Barlıq waqıtlar is waqtı (Asia/Tashkent).
Bul bolmastan burın jasalǵan bronlarda keliw waqtı joq hám bul jerde hesh qashan biykar etilmeydi.
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
    """Bir yamasa birneshe kelmegen bron biykar etilmegen isleniwden keyin kóteriledi."""


def arrival_deadline(booking):
    """Mehmann kelmedi dep esaplanatuǵın waqıt, yamasa keliw waqtı berilmegen bolsa None."""
    if booking.expected_arrival_time is None:
        return None
    start = datetime.combine(booking.check_in, booking.expected_arrival_time, tzinfo=business_time_zone())
    return start + timedelta(hours=settings.ARRIVAL_GRACE_HOURS)


def arrival_time_error(check_in: date, arrival: time, now=None):
    """Mehmann búgin ótip ketken waqıtta keletuǵın bolsa xabar, bolmasa None."""
    now = (now or timezone.now()).astimezone(business_time_zone())
    if check_in == now.date() and arrival <= now.time().replace(tzinfo=None):
        return 'The arrival time has already passed today.'
    return None


def mark_arrived(booking, now=None):
    """Mehmanxana mehmannıń kelgenin aytadı. Idempotent: birinshi ret saqlanadı. ValueError nege islep bolmaytuǵının aytadı."""
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
    """Keliw múddetinen ótken hár tastıyıqlanǵan bronnı biykar etiw. {'cancelled': n, 'failed': n} qaytaradı."""
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
