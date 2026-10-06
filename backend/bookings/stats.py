"""
Booking statistics shared by the admin and partner Status sections.

R12: the definitions live in bookings/metrics.py (guests = persons, unique customers,
nights, stays, the refund rule, revenue = paid - refunded per currency, periods, series).
This module keeps the old public names as thin wrappers so older callers keep working:

- parse_period, parse_year, InvalidPeriod, counted_q, counted_bookings, available_years,
  COUNTED_STATUSES, PERIOD_ALL: re-exported from metrics.
- revenue_by / revenue_total / metric_totals(bookings): the PRE-R12 shape over an
  already-filtered queryset - `revenue` there is the booking value (SUM(total_price) per
  booking currency, metrics.booking_value_*) and `guests` the distinct accounts
  (metrics `unique_customers`). The Status views use metrics directly.

All aggregation runs in the database; Python only reshapes already-aggregated rows.
"""
from django.db.models import Count

from bookings.metrics import (  # noqa: F401  (re-exported)
    COUNTED_STATUSES, PERIOD_ALL, InvalidPeriod, available_years, booking_value_by, booking_value_total,
    counted_bookings, counted_q, parse_period, parse_year,
)


def commission_amount(gross_revenue, currency):
    """
    Platform commission on gross booking value.

    COMMISSION IS NOT DEFINED YET: this is the one place to add the rule.
    Returns None until then, and the Status views do not report a commission.
    """
    return None


def revenue_by(bookings, key):
    """{key value: [{'currency', 'amount'}, ...]} of booking value (pre-R12 `revenue`)."""
    return booking_value_by(bookings, key)


def revenue_total(bookings):
    """[{'currency', 'amount'}, ...] of booking value (pre-R12 `revenue`)."""
    return booking_value_total(bookings)


def metric_totals(bookings):
    """Pre-R12 {'bookings', 'guests' (distinct accounts), 'revenue' (booking value)}."""
    totals = bookings.aggregate(bookings=Count('id'), guests=Count('guest', distinct=True))
    return {'bookings': totals['bookings'], 'guests': totals['guests'], 'revenue': revenue_total(bookings)}
