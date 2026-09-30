"""
Booking statistics shared by the admin and partner Status sections.

Definitions (see .ai/STATUS_PLAN.md):
- A booking COUNTS when its status is confirmed or completed (not pending, cancelled
  or no_show) and it is not soft-deleted.
- A booking belongs to the period that contains its CHECK-IN date.
- Revenue = sum of `total_price` of counted bookings (gross booking value), always
  grouped per currency, never mixed.
- Guests = distinct guest accounts with at least one counted booking.

All aggregation runs in the database; Python only reshapes already-aggregated rows.
"""
import re
from datetime import date

from django.db.models import Count, Q, Sum
from django.db.models.functions import ExtractMonth

COUNTED_STATUSES = ('confirmed', 'completed')

PERIOD_ALL = 'all'
_PERIOD_RE = re.compile(r'^(?P<year>\d{4})(?:-(?P<month>\d{2}))?$')


def commission_amount(gross_revenue, currency):
    """
    Platform commission on gross booking value.

    COMMISSION IS NOT DEFINED YET: this is the one place to add the rule.
    Returns None until then, and the Status views do not report a commission.
    """
    return None


class InvalidPeriod(ValueError):
    pass


def parse_period(value):
    """
    'all' (or empty) -> None; 'YYYY' -> that year; 'YYYY-MM' -> that month.

    Returns (label, (first_day, first_day_after)) or (PERIOD_ALL, None).
    Raises InvalidPeriod for anything else.
    """
    value = (value or PERIOD_ALL).strip()
    if value == PERIOD_ALL:
        return PERIOD_ALL, None
    match = _PERIOD_RE.match(value)
    if not match:
        raise InvalidPeriod('period must be "all", a year (YYYY) or a month (YYYY-MM).')
    year = int(match['year'])
    if not 2000 <= year <= 2100:
        raise InvalidPeriod('period year must be between 2000 and 2100.')
    if match['month'] is None:
        return value, (date(year, 1, 1), date(year + 1, 1, 1))
    month = int(match['month'])
    if not 1 <= month <= 12:
        raise InvalidPeriod('period month must be between 01 and 12.')
    after = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return value, (date(year, month, 1), after)


def parse_year(value, default):
    """A year for monthly series; InvalidPeriod when it is not YYYY."""
    if value in (None, ''):
        return default
    if not re.fullmatch(r'\d{4}', str(value)) or not 2000 <= int(value) <= 2100:
        raise InvalidPeriod('year must be a year between 2000 and 2100 (YYYY).')
    return int(value)


def counted_q(prefix='', date_range=None):
    """Q for counted bookings; `prefix` is the path to Booking, e.g. 'bookings__'."""
    q = Q(**{f'{prefix}status__in': COUNTED_STATUSES, f'{prefix}is_deleted': False})
    if date_range:
        first, after = date_range
        q &= Q(**{f'{prefix}check_in__gte': first, f'{prefix}check_in__lt': after})
    return q


def counted_bookings(date_range=None):
    """Booking queryset of counted bookings (in `date_range` when given)."""
    from bookings.models import Booking

    return Booking.objects.filter(counted_q('', date_range))


def metric_annotations(prefix='bookings__', date_range=None):
    """Counted bookings and distinct guests, for .annotate() on a query grouped by something."""
    counted = counted_q(prefix, date_range)
    return {
        'bookings_count': Count(f'{prefix}id', filter=counted, distinct=True),
        'guests_count': Count(f'{prefix}guest', filter=counted, distinct=True),
    }


def revenue_by(bookings, key):
    """
    {key value: [{'currency', 'amount'}, ...]} for already-filtered counted bookings.

    `key` is a Booking lookup (e.g. 'property__country') or an annotation name.
    One aggregated row per (key, currency).
    """
    rows = bookings.values(key, 'currency').annotate(amount=Sum('total_price')).order_by(key, 'currency')
    result = {}
    for row in rows:
        result.setdefault(row[key], []).append({'currency': row['currency'], 'amount': str(row['amount'])})
    return result


def revenue_total(bookings):
    """[{'currency', 'amount'}, ...] for already-filtered counted bookings."""
    rows = bookings.values('currency').annotate(amount=Sum('total_price')).order_by('currency')
    return [{'currency': row['currency'], 'amount': str(row['amount'])} for row in rows]


def metric_totals(bookings):
    """{'bookings', 'guests', 'revenue'} for already-filtered counted bookings."""
    totals = bookings.aggregate(bookings=Count('id'), guests=Count('guest', distinct=True))
    return {'bookings': totals['bookings'], 'guests': totals['guests'], 'revenue': revenue_total(bookings)}


def available_years(bookings):
    """Years (ascending) that have at least one counted booking, for the year selector."""
    return [day.year for day in bookings.dates('check_in', 'year')]


def monthly_series(bookings, year):
    """
    Twelve rows for `year` ({'month': 'YYYY-MM', 'bookings', 'guests', 'revenue'}),
    months without bookings included with zeros. `bookings` are counted bookings.
    """
    in_year = bookings.filter(check_in__year=year).annotate(month=ExtractMonth('check_in'))
    counts = {
        row['month']: row
        for row in in_year.values('month').annotate(
            bookings_count=Count('id'), guests_count=Count('guest', distinct=True)).order_by('month')
    }
    revenue = revenue_by(in_year, 'month')
    series = []
    for month in range(1, 13):
        row = counts.get(month, {})
        series.append({
            'month': f'{year}-{month:02d}',
            'bookings': row.get('bookings_count', 0),
            'guests': row.get('guests_count', 0),
            'revenue': revenue.get(month, []),
        })
    return series
