"""
Free cancellation and the refund of a guest who cancels a paid booking (R11, .ai/PLAN_R11_CANCELLATION.md).

The terms of a rate plan (a free window in hours before the check-in day, and the percent that comes back
after it) are copied onto the booking when it is created. This module is the only place with the rule:

terms_for_plan()      the snapshot a new booking stores
free_until()          the moment the free window ends
refund_percent_at()   what share of the amount paid a cancellation at `now` gets back (None = no promise)
"""
from datetime import datetime, time, timedelta

from django.conf import settings

from common.dates import business_time_zone


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
