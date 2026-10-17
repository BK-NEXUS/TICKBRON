"""
Free cancellation and the refund of a guest who cancels a paid booking (R11, .ai/PLAN_R11_CANCELLATION.md).

The terms of a rate plan (a free window in hours before the check-in day, and the percent that comes back
after it) are copied onto the booking when it is created. This module is the only place with the rule:

terms_for_plan()      the snapshot a new booking stores
free_until()          the moment the free window ends
refund_percent_at()   what share of the amount paid a cancellation at `now` gets back (None = no promise)
cancel_preview()      the refund a cancellation right now would give, changing nothing
cancel_with_refund()  the guest's cancellation: cancel + refund rows in one transaction
"""
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from common.dates import business_time_zone
from common.money import CHARGE_CURRENCY


def free_until(check_in, free_cancel_hours):
    """The end of the free window: `free_cancel_hours` before the start of the check-in day (business time)."""
    if free_cancel_hours is None:
        return None
    day_start = datetime.combine(check_in, time.min, tzinfo=business_time_zone())
    return day_start - timedelta(hours=free_cancel_hours)


def terms_for_plan(rate_plan, check_in):
    """(free_until, refund_percent_after) a booking of this rate plan stores. 0 percent is a real answer."""
    percent = rate_plan.cancel_refund_percent
    if percent is None:
        percent = settings.CANCEL_REFUND_PERCENT
    return free_until(check_in, rate_plan.free_cancel_hours), percent


def refund_percent_at(booking, now):
    """100 inside the free window, else the stored percent; None for a booking made before the terms existed."""
    percent_after = booking.cancel_refund_percent_after
    if percent_after is None:
        return None
    if booking.cancel_free_until is not None and now <= booking.cancel_free_until:
        return 100
    return percent_after


def cancellation_terms(booking):
    """What the guest was promised, for the booking responses; None for a booking without a snapshot."""
    if booking.cancel_refund_percent_after is None:
        return None
    return {
        'free_until': booking.cancel_free_until.isoformat() if booking.cancel_free_until else None,
        'refund_percent_after': booking.cancel_refund_percent_after,
    }


def _refund_amount(booking, percent):
    from bookings.noshow import paid_and_refunded, refund_now

    paid, already = paid_and_refunded([booking.pk])
    return refund_now(paid.get(booking.pk) or Decimal('0'), already.get(booking.pk) or Decimal('0'), percent or 0)


def _result(amount, percent):
    return {'amount': f'{amount:.2f}', 'currency': CHARGE_CURRENCY, 'percent': percent}


def cancel_preview(booking, now=None):
    """What cancelling right now would give back (nothing is changed)."""
    percent = refund_percent_at(booking, now or timezone.now())
    return {
        'refund_amount': f'{_refund_amount(booking, percent):.2f}',
        'refund_currency': CHARGE_CURRENCY,
        'refund_percent': percent,
        'free_until': booking.cancel_free_until.isoformat() if booking.cancel_free_until else None,
    }


def cancel_with_refund(booking, reason=None, actor=None, now=None):
    """
    The guest cancels: the booking is cancelled and inventory released (Booking.cancel_booking) and, when the
    terms promise something, the refund is created, all in ONE transaction. The provider is asked after commit.
    Returns {amount, currency, percent} of what was refunded. Raises what cancel_booking raises.
    """
    from bookings.noshow import refund_allocations, send_after_commit
    from payments.refunds import create_refund

    with transaction.atomic():
        booking.cancel_booking(reason)
        percent = refund_percent_at(booking, now or timezone.now())
        refunds = []
        for index, (payment, amount) in enumerate(refund_allocations(booking, percent or 0)):
            key = f'{booking.pk}:cancel' if index == 0 else f'{booking.pk}:cancel:{payment.pk}'
            refunds.append(create_refund(payment, amount, 'cancel', created_by=actor, idempotency_key=key))
        send_after_commit(refunds, actor)
    return _result(sum((refund.amount for refund in refunds), Decimal('0')), percent)
