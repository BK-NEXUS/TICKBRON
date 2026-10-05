"""Shared helpers for the R12 tests: bookings written directly (past stays, any status)."""
from datetime import datetime, time, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest import mock
import zoneinfo

from bookings.models import Booking

TASHKENT = zoneinfo.ZoneInfo('Asia/Tashkent')


def at_tashkent(day, hour, minute=0):
    """Patch "now" to a local Tashkent time on `day`."""
    moment = datetime.combine(day, time(hour, minute), tzinfo=TASHKENT).astimezone(dt_timezone.utc)
    return mock.patch('django.utils.timezone.now', return_value=moment)


def make_booking(prop, guest, check_in, nights=2, status='confirmed', rooms=1, guest_count=1,
                 price=Decimal('500000'), currency='UZS', payment_status=None):
    """A booking row as the engine leaves it (no inventory; for status and statistics tests)."""
    if payment_status is None:
        payment_status = 'paid' if status in ('confirmed', 'completed', 'no_show') else 'pending'
    return Booking.objects.create(
        guest=guest, property=prop, status=status, payment_status=payment_status,
        check_in=check_in, check_out=check_in + timedelta(days=nights), number_of_nights=nights,
        number_of_rooms=rooms, guest_count=guest_count, total_price=price * nights * rooms, currency=currency,
        guest_full_name='Test Guest', guest_email=guest.email, expires_at=None,
    )
