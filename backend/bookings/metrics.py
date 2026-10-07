"""
Status definitions (R12 phase 2, .ai/PLAN_R12.md section 1). The one place that says what
a guest, a stay, a night and revenue are; bookings/stats.py keeps its old public names as
thin wrappers, and every Status view (admin and partner) reads these functions.

- Date basis: the CHECK-IN date. "Today" = common.dates.business_today() (Asia/Tashkent).
- counted   = confirmed + completed, not soft-deleted, not fully refunded.
- stayed    = completed, not fully refunded (the headline number).
- upcoming  = confirmed with check-in after today; never limited by the period.
- bookings  = COUNT of counted bookings.
- every headline number also exists as PERSONS (SUM(guest_count)): counted_guests (= guests),
              stayed_guests (completed) and upcoming_guests (upcoming); the reconciliation blocks
              carry bookings and guests for counted and stayed.
- guests    = SUM(guest_count) of counted bookings (persons; guest_count includes children).
- unique_customers = COUNT(DISTINCT guest) of counted bookings (the old `guests`).
- nights    = SUM(number_of_nights); room_nights = SUM(number_of_nights x number_of_rooms).
- no_show   = status no_show (an approved report), not fully refunded; no_show_reported = has a
              pending no-show report. A reported booking is neither stayed nor no_show until staff
              decide: it is left out of the confirmed / completed counts of booking_status.
- fully_refunded = counted or no_show bookings excluded by the refund rule: the booking has
              at least one paid payment and every paid payment is refunded in full by
              `succeeded` Refund rows (per payment, so per currency too). Failed, pending or
              needs_manual refunds never count.
- revenue   = per currency, never mixed: SUM(paid payments) - SUM(succeeded refunds) of the
              counted + no_show bookings (a no-show keeps what was not refunded). A booking
              without payment rows (legacy / demo) counts with revenue 0.
- booking_value = SUM(total_price) of counted bookings in the hotel's currency (the old
              `revenue`).
- booking_status = raw counts per status in the period: pending, confirmed, completed,
              cancelled (not expired), expired (cancelled by expiry, EXPIRY_REASON), no_show,
              no_show_reported.

Caveat: "stayed" numbers for the last NO_SHOW_REPORT_WINDOW_DAYS days after check-out can
still change: a hotel may report a no-show in that window, and an approved report moves the
booking from stayed to no_show. (A completed stay with a PENDING report is still in `stayed`
until it is decided.)

All aggregation runs in the database; Python only reshapes already-aggregated rows.
"""
import re
from datetime import date, timedelta

from django.conf import settings
from django.db.models import Count, Exists, F, IntegerField, Max, Min, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce, TruncDay, TruncMonth, TruncWeek, TruncYear

from common.dates import business_today

COUNTED_STATUSES = ('confirmed', 'completed')
REVENUE_STATUSES = ('confirmed', 'completed', 'no_show')
PAID_PAYMENT_STATUSES = ('completed', 'refunded', 'partially_refunded')
EXPIRY_REASON = 'Booking expired - payment not completed within time limit'
BOOKING_STATUS_KEYS = ('pending', 'confirmed', 'completed', 'cancelled', 'expired', 'no_show', 'no_show_reported')

MAX_CUSTOM_YEARS = 20
MAX_BUCKETS = 1000
GRANULARITIES = ('day', 'week', 'month', 'year')

PERIOD_ALL = 'all'
NAMED_PERIODS = ('today', 'last_7_days', 'last_30_days', 'this_year', 'last_5_years', 'last_10_years', 'custom')
_PERIOD_RE = re.compile(r'^(?P<year>\d{4})(?:-(?P<month>\d{2}))?$')


class InvalidPeriod(ValueError):
    pass


def status_meta(today=None):
    """The meta every statistics response carries: the business date the numbers are as of and
    the window in which a hotel can still report a no-show (so "stayed" can still change)."""
    return {
        'business_date': (today or business_today()).isoformat(),
        'no_show_report_window_days': settings.NO_SHOW_REPORT_WINDOW_DAYS,
    }


# --- periods -------------------------------------------------------------------------

def _years_back(day, years):
    try:
        return day.replace(year=day.year - years)
    except ValueError:      # 29 February
        return day.replace(year=day.year - years, day=28)


def _years_ahead(day, years):
    try:
        return day.replace(year=day.year + years)
    except ValueError:
        return day.replace(year=day.year + years, day=28)


def _iso_date(value, field):
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise InvalidPeriod(f'{field} must be a date (YYYY-MM-DD).')


def parse_period(value, date_from=None, date_to=None, today=None):
    """
    Returns (label, (first_day, first_day_after)) or (PERIOD_ALL, None).

    'all' (or empty), 'today', 'last_7_days' (today-6 .. today), 'last_30_days',
    'this_year' (1 Jan .. 31 Dec), 'last_5_years' / 'last_10_years' (same day N years ago
    + 1 day .. today), 'custom' with `date_from` / `date_to` (inclusive, from <= to, at
    most 20 years), 'YYYY', 'YYYY-MM'. Raises InvalidPeriod for anything else.
    """
    value = (value or PERIOD_ALL).strip()
    today = today or business_today()
    after_today = today + timedelta(days=1)
    if value == PERIOD_ALL:
        return PERIOD_ALL, None
    if value == 'today':
        return value, (today, after_today)
    if value == 'last_7_days':
        return value, (today - timedelta(days=6), after_today)
    if value == 'last_30_days':
        return value, (today - timedelta(days=29), after_today)
    if value == 'this_year':
        return value, (date(today.year, 1, 1), date(today.year + 1, 1, 1))
    if value in ('last_5_years', 'last_10_years'):
        years = 5 if value == 'last_5_years' else 10
        return value, (_years_back(today, years) + timedelta(days=1), after_today)
    if value == 'custom':
        if not date_from or not date_to:
            raise InvalidPeriod('custom period needs from and to (YYYY-MM-DD).')
        first, last = _iso_date(date_from, 'from'), _iso_date(date_to, 'to')
        if first > last:
            raise InvalidPeriod('from must not be after to.')
        if last >= _years_ahead(first, MAX_CUSTOM_YEARS):
            raise InvalidPeriod(f'custom period can be at most {MAX_CUSTOM_YEARS} years.')
        return value, (first, last + timedelta(days=1))
    match = _PERIOD_RE.match(value)
    if not match:
        raise InvalidPeriod(
            'period must be "all", "today", "last_7_days", "last_30_days", "this_year", '
            '"last_5_years", "last_10_years", "custom", a year (YYYY) or a month (YYYY-MM).')
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


def period_from_request(request):
    """(label, date_range) from ?period=, ?from=, ?to=. Raises InvalidPeriod."""
    params = request.query_params
    return parse_period(params.get('period'), params.get('from'), params.get('to'))


def range_json(date_range):
    """{'from', 'to'} (inclusive ISO dates) or None for all time."""
    if date_range is None:
        return None
    first, after = date_range
    return {'from': first.isoformat(), 'to': (after - timedelta(days=1)).isoformat()}


def parse_year(value, default):
    """A year for monthly series; InvalidPeriod when it is not YYYY."""
    if value in (None, ''):
        return default
    if not re.fullmatch(r'\d{4}', str(value)) or not 2000 <= int(value) <= 2100:
        raise InvalidPeriod('year must be a year between 2000 and 2100 (YYYY).')
    return int(value)


# --- granularity and buckets ---------------------------------------------------------

def bucket_start(day, granularity):
    if granularity == 'day':
        return day
    if granularity == 'week':
        return day - timedelta(days=day.weekday())
    if granularity == 'month':
        return day.replace(day=1)
    return day.replace(month=1, day=1)


def _next_bucket(start, granularity):
    if granularity == 'day':
        return start + timedelta(days=1)
    if granularity == 'week':
        return start + timedelta(days=7)
    if granularity == 'month':
        return date(start.year + 1, 1, 1) if start.month == 12 else date(start.year, start.month + 1, 1)
    return date(start.year + 1, 1, 1)


def bucket_label(start, granularity):
    if granularity in ('day', 'week'):
        return start.isoformat()
    if granularity == 'month':
        return f'{start.year}-{start.month:02d}'
    return str(start.year)


def buckets(date_range, granularity):
    """Bucket start dates covering [first, after). InvalidPeriod above MAX_BUCKETS."""
    first, after = date_range
    starts = []
    start = bucket_start(first, granularity)
    while start < after:
        starts.append(start)
        if len(starts) > MAX_BUCKETS:
            raise InvalidPeriod(f'at most {MAX_BUCKETS} {granularity} buckets; choose a coarser granularity.')
        start = _next_bucket(start, granularity)
    return starts


def parse_granularity(value, default='month'):
    value = (value or default).strip()
    if value not in GRANULARITIES:
        raise InvalidPeriod('granularity must be day, week, month or year.')
    return value


_TRUNC = {'day': TruncDay, 'week': TruncWeek, 'month': TruncMonth, 'year': TruncYear}


# --- the refund rule ------------------------------------------------------------------

def fully_refunded_booking_ids():
    """
    Subquery of booking ids that are fully refunded: at least one paid payment, and no
    paid payment with money left after its `succeeded` refunds.

    The refunds of one payment never exceed it (payments.refunds.create_refund checks it with
    the payment locked; the backfill skips such rows), so "every paid payment is refunded in
    full" is the same as "succeeded refunds of paid payments >= everything paid". Only bookings
    with a succeeded refund are looked at, which keeps the subquery small.
    """
    from payments.models import PaymentTransaction, Refund

    paid = (PaymentTransaction.objects.filter(booking_id=OuterRef('booking_id'), status__in=PAID_PAYMENT_STATUSES)
            .values('booking_id').annotate(total=Sum('amount')).values('total'))
    return (
        Refund.objects.filter(status='succeeded', payment__status__in=PAID_PAYMENT_STATUSES)
        .values('booking_id')
        .annotate(refunded=Sum('amount'))
        .filter(refunded__gte=Subquery(paid))
        .values('booking_id')
    )


def fully_refunded_ids(scope):
    """
    Ids of the fully refunded bookings in `scope` (one query). The aggregates below take this
    list instead of the subquery: Postgres would rebuild the subquery's hash for every FILTER
    clause (about 25 ms each on 50k bookings, see the R12 checkpoint).
    """
    return list(scope.filter(fully_refunded_q()).values_list('id', flat=True))


def fully_refunded_q(prefix='', refunded_ids=None):
    """Q for fully refunded bookings; with `refunded_ids` (fully_refunded_ids()) a plain id list."""
    if refunded_ids is None:
        return Q(**{f'{prefix}id__in': fully_refunded_booking_ids()})
    if not refunded_ids:
        return Q(**{f'{prefix}id': -1})    # no booking has this id: nothing is fully refunded
    return Q(**{f'{prefix}id__in': refunded_ids})


# --- booking sets -------------------------------------------------------------------

def period_q(prefix='', date_range=None):
    if not date_range:
        return Q()
    first, after = date_range
    return Q(**{f'{prefix}check_in__gte': first, f'{prefix}check_in__lt': after})


def counted_q(prefix='', date_range=None, refunded_ids=None):
    """Q for counted bookings; `prefix` is the path to Booking, e.g. 'bookings__'."""
    return (Q(**{f'{prefix}status__in': COUNTED_STATUSES, f'{prefix}is_deleted': False})
            & period_q(prefix, date_range) & ~fully_refunded_q(prefix, refunded_ids))


def revenue_q(prefix='', date_range=None, refunded_ids=None):
    """Bookings whose money is revenue: counted + no_show, not fully refunded."""
    return (Q(**{f'{prefix}status__in': REVENUE_STATUSES, f'{prefix}is_deleted': False})
            & period_q(prefix, date_range) & ~fully_refunded_q(prefix, refunded_ids))


def _bookings():
    from bookings.models import Booking
    return Booking.objects.all()


def counted_bookings(date_range=None):
    return _bookings().filter(counted_q('', date_range))


def revenue_bookings(date_range=None):
    return _bookings().filter(revenue_q('', date_range))


def all_bookings():
    """Every not-deleted booking (the base for booking_status and conditional totals)."""
    return _bookings().filter(is_deleted=False)


# --- grouped annotations (on a query of Property, User, ...) ---------------------------

def upcoming_q(prefix='', today=None):
    """Confirmed bookings checking in after today, not fully refunded; never limited by a period."""
    today = today or business_today()
    return (Q(**{f'{prefix}status': 'confirmed', f'{prefix}is_deleted': False, f'{prefix}check_in__gt': today})
            & ~fully_refunded_q(prefix))


def guest_annotations(prefix='bookings__', date_range=None, refunded_ids=None, today=None):
    """Persons (SUM guest_count) of counted, stayed and upcoming bookings, for .annotate()."""
    counted = counted_q(prefix, date_range, refunded_ids)
    return {
        'counted_guests_count': Coalesce(Sum(f'{prefix}guest_count', filter=counted), 0),
        'stayed_guests_count': Coalesce(
            Sum(f'{prefix}guest_count', filter=counted & Q(**{f'{prefix}status': 'completed'})), 0),
        'upcoming_guests_count': Coalesce(Sum(f'{prefix}guest_count', filter=upcoming_q(prefix, today)), 0),
    }


def metric_annotations(prefix='bookings__', date_range=None, refunded_ids=None, today=None):
    """
    Counted bookings, guests, unique customers, nights, room nights and stays, for .annotate().
    Pass `refunded_ids` (fully_refunded_ids()) so the refund rule is not re-run per aggregate.
    """
    counted = counted_q(prefix, date_range, refunded_ids)
    return {
        'bookings_count': Count(f'{prefix}id', filter=counted, distinct=True),
        'guests_count': Coalesce(Sum(f'{prefix}guest_count', filter=counted), 0),
        'unique_customers_count': Count(f'{prefix}guest', filter=counted, distinct=True),
        'nights_count': Coalesce(Sum(f'{prefix}number_of_nights', filter=counted), 0),
        'room_nights_count': Coalesce(
            Sum(F(f'{prefix}number_of_nights') * F(f'{prefix}number_of_rooms'), filter=counted,
                output_field=IntegerField()), 0),
        'stayed_count': Count(f'{prefix}id', filter=counted & Q(**{f'{prefix}status': 'completed'}), distinct=True),
        **guest_annotations(prefix, date_range, refunded_ids, today),
    }


def grouped_row(item):
    """The metric fields of a row annotated with metric_annotations()."""
    return {
        'bookings': item['bookings_count'],
        'guests': item['guests_count'],
        'unique_customers': item['unique_customers_count'],
        'nights': item['nights_count'],
        'room_nights': item['room_nights_count'],
        'stayed': item['stayed_count'],
        **guest_fields(item),
    }


def guest_fields(item):
    """The persons fields of a row annotated with guest_annotations()."""
    return {
        'counted_guests': item['counted_guests_count'],
        'stayed_guests': item['stayed_guests_count'],
        'upcoming_guests': item['upcoming_guests_count'],
    }


# --- money --------------------------------------------------------------------------

def _money(amount):
    return f'{amount:.2f}'


def revenue_by(bookings, key):
    """
    {key value: [{'currency', 'amount'}, ...]}: paid payments minus succeeded refunds, per
    currency, for already-filtered revenue bookings. `key` is a Booking lookup or annotation.
    Two aggregated queries (payments, refunds); currencies without a paid payment are left out.
    """
    paid_rows = (bookings.values(key, 'payment_transactions__currency')
                 .annotate(amount=Sum('payment_transactions__amount',
                                      filter=Q(payment_transactions__status__in=PAID_PAYMENT_STATUSES)))
                 .order_by())
    refunded_rows = (bookings.filter(refunds__status='succeeded')
                     .values(key, 'refunds__currency').annotate(amount=Sum('refunds__amount')).order_by())
    paid = {}
    for row in paid_rows:
        if row['payment_transactions__currency'] and row['amount'] is not None:
            paid[(row[key], row['payment_transactions__currency'])] = row['amount']
    for row in refunded_rows:
        pair = (row[key], row['refunds__currency'])
        if pair in paid:
            paid[pair] -= row['amount']
    result = {}
    for (group, currency), amount in sorted(paid.items(), key=lambda item: (str(item[0][0]), item[0][1])):
        result.setdefault(group, []).append({'currency': currency, 'amount': _money(amount)})
    return result


def revenue_total(bookings):
    """[{'currency', 'amount'}, ...] for already-filtered revenue bookings."""
    return revenue_by(bookings.annotate(_all=Value(1, output_field=IntegerField())), '_all').get(1, [])


def booking_value_by(bookings, key):
    """{key value: [{'currency', 'amount'}]}: SUM(total_price) per booking currency (old revenue)."""
    rows = bookings.values(key, 'currency').annotate(amount=Sum('total_price')).order_by(key, 'currency')
    result = {}
    for row in rows:
        result.setdefault(row[key], []).append({'currency': row['currency'], 'amount': _money(row['amount'])})
    return result


def booking_value_total(bookings):
    rows = bookings.values('currency').annotate(amount=Sum('total_price')).order_by('currency')
    return [{'currency': row['currency'], 'amount': _money(row['amount'])} for row in rows]


# --- totals -------------------------------------------------------------------------

def _pending_report():
    from bookings.models import NoShowReport
    return Exists(NoShowReport.objects.filter(booking_id=OuterRef('pk'), status='pending'))


def _status_counts(date_range):
    in_period = period_q('', date_range)
    reported = Q(_pending_report())
    expired = Q(status='cancelled', cancellation_reason=EXPIRY_REASON)
    return {
        'st_pending': Count('id', filter=in_period & Q(status='pending')),
        'st_confirmed': Count('id', filter=in_period & Q(status='confirmed') & ~reported),
        'st_completed': Count('id', filter=in_period & Q(status='completed') & ~reported),
        'st_reported': Count('id', filter=in_period & reported),
        'st_cancelled': Count('id', filter=in_period & Q(status='cancelled') & ~expired),
        'st_expired': Count('id', filter=in_period & expired),
        'st_no_show': Count('id', filter=in_period & Q(status='no_show')),
    }


def metric_totals(scope, date_range=None, today=None, refunded_ids=None):
    """
    Every number of section 1 for the bookings in `scope` (a not-deleted Booking queryset
    narrowed to a hotel, an owner or a guest; NOT narrowed to the period). One aggregate
    query for the counts plus two for revenue and one for booking value.
    """
    today = today or business_today()
    if refunded_ids is None:
        refunded_ids = fully_refunded_ids(scope)
    counted = counted_q('', date_range, refunded_ids)
    in_period = period_q('', date_range)
    refunded = fully_refunded_q('', refunded_ids)
    upcoming = Q(status='confirmed', check_in__gt=today) & ~refunded
    totals = scope.aggregate(
        bookings=Count('id', filter=counted),
        guests=Coalesce(Sum('guest_count', filter=counted), 0),
        unique_customers=Count('guest', filter=counted, distinct=True),
        nights=Coalesce(Sum('number_of_nights', filter=counted), 0),
        room_nights=Coalesce(Sum(F('number_of_nights') * F('number_of_rooms'), filter=counted,
                                 output_field=IntegerField()), 0),
        stayed=Count('id', filter=counted & Q(status='completed')),
        stayed_guests=Coalesce(Sum('guest_count', filter=counted & Q(status='completed')), 0),
        upcoming=Count('id', filter=upcoming),
        upcoming_guests=Coalesce(Sum('guest_count', filter=upcoming), 0),
        no_show=Count('id', filter=in_period & Q(status='no_show') & ~refunded),
        fully_refunded=Count('id', filter=in_period & Q(status__in=REVENUE_STATUSES) & refunded),
        **_status_counts(date_range),
    )
    in_revenue = scope.filter(revenue_q('', date_range, refunded_ids))
    in_counted = scope.filter(counted)
    return {
        'bookings': totals['bookings'],
        'stayed': totals['stayed'],
        'counted': totals['bookings'],
        'guests': totals['guests'],
        'counted_guests': totals['guests'],
        'stayed_guests': totals['stayed_guests'],
        'upcoming_guests': totals['upcoming_guests'],
        'unique_customers': totals['unique_customers'],
        'nights': totals['nights'],
        'room_nights': totals['room_nights'],
        'no_show': totals['no_show'],
        'no_show_reported': totals['st_reported'],
        'fully_refunded': totals['fully_refunded'],
        'upcoming': totals['upcoming'],
        'revenue': revenue_total(in_revenue),
        'booking_value': booking_value_total(in_counted),
        'booking_status': {
            'pending': totals['st_pending'], 'confirmed': totals['st_confirmed'],
            'completed': totals['st_completed'], 'cancelled': totals['st_cancelled'],
            'expired': totals['st_expired'], 'no_show': totals['st_no_show'],
            'no_show_reported': totals['st_reported'],
        },
    }


# --- series -------------------------------------------------------------------------

def series(scope, date_range, granularity, today=None, refunded_ids=None):
    """
    One row per bucket ({'period', 'start', 'bookings', 'guests', 'nights', 'stayed',
    'revenue'}), empty buckets included. With date_range None the range runs from the first
    check-in of `scope` to today (or the last check-in when later). InvalidPeriod above
    MAX_BUCKETS buckets.
    """
    today = today or business_today()
    if refunded_ids is None:
        refunded_ids = fully_refunded_ids(scope)
    if date_range is None:
        span = scope.filter(counted_q('', None, refunded_ids)).aggregate(first=Min('check_in'), last=Max('check_in'))
        if span['first'] is None:
            return []
        date_range = (span['first'], max(span['last'], today) + timedelta(days=1))
    starts = buckets(date_range, granularity)
    trunc = _TRUNC[granularity]('check_in')
    counted = scope.filter(counted_q('', date_range, refunded_ids)).annotate(bucket=trunc)
    counts = {
        _as_date(row['bucket']): row
        for row in counted.values('bucket').annotate(
            n=Count('id'), g=Coalesce(Sum('guest_count'), 0), nights=Coalesce(Sum('number_of_nights'), 0),
            stayed=Count('id', filter=Q(status='completed')),
        ).order_by('bucket')
    }
    money = revenue_by(scope.filter(revenue_q('', date_range, refunded_ids)).annotate(bucket=trunc), 'bucket')
    money = {_as_date(key): value for key, value in money.items()}
    rows = []
    for start in starts:
        row = counts.get(start, {})
        rows.append({
            'period': bucket_label(start, granularity), 'start': start.isoformat(),
            'bookings': row.get('n', 0), 'guests': row.get('g', 0), 'nights': row.get('nights', 0),
            'stayed': row.get('stayed', 0), 'revenue': money.get(start, []),
        })
    return rows


def _as_date(value):
    return value.date() if hasattr(value, 'date') and callable(value.date) else value


def monthly_series(scope, year, refunded_ids=None):
    """
    Twelve rows for `year` ({'month': 'YYYY-MM', 'bookings', 'guests', 'revenue'}), kept for
    the existing `monthly` field. `scope` is a not-deleted Booking queryset.
    """
    rows = series(scope, (date(year, 1, 1), date(year + 1, 1, 1)), 'month', refunded_ids=refunded_ids)
    return [{'month': row['period'], 'bookings': row['bookings'], 'guests': row['guests'],
             'nights': row['nights'], 'stayed': row['stayed'], 'revenue': row['revenue']} for row in rows]


def available_years(scope, refunded_ids=None):
    """Years (ascending) that have at least one counted booking, for the year selector."""
    return [day.year for day in scope.filter(counted_q('', None, refunded_ids)).dates('check_in', 'year')]


# --- reconciliation -----------------------------------------------------------------

def reconciliation_windows(today=None):
    today = today or business_today()
    monday = today - timedelta(days=today.weekday())
    month_after = date(today.year + 1, 1, 1) if today.month == 12 else date(today.year, today.month + 1, 1)
    return {
        'today': (today, today + timedelta(days=1)),
        'this_week': (monday, monday + timedelta(days=7)),
        'this_month': (today.replace(day=1), month_after),
        'this_year': (date(today.year, 1, 1), date(today.year + 1, 1, 1)),
        'all_time': None,
    }


def _reconciliation_aggregates(windows, refunded_ids):
    aggregates = {}
    for name, window in windows.items():
        counted = counted_q('', window, refunded_ids)
        stayed = counted & Q(status='completed')
        aggregates[f'{name}__cb'] = Count('id', filter=counted)
        aggregates[f'{name}__cg'] = Coalesce(Sum('guest_count', filter=counted), 0)
        aggregates[f'{name}__sb'] = Count('id', filter=stayed)
        aggregates[f'{name}__sg'] = Coalesce(Sum('guest_count', filter=stayed), 0)
    return aggregates


def _reconciliation_block(windows, values):
    return {
        name: {
            **(range_json(window) or {'from': None, 'to': None}),
            'counted': {'bookings': values[f'{name}__cb'], 'guests': values[f'{name}__cg']},
            'stayed': {'bookings': values[f'{name}__sb'], 'guests': values[f'{name}__sg']},
        }
        for name, window in windows.items()
    }


def reconciliation(scope, today=None, refunded_ids=None):
    """
    {window: {'from', 'to', 'counted': {bookings, guests}, 'stayed': {bookings, guests}}}
    for today, this week (Mon-Sun), this month, this year and all time. One query.
    """
    windows = reconciliation_windows(today)
    if refunded_ids is None:
        refunded_ids = fully_refunded_ids(scope)
    aggregates = _reconciliation_aggregates(windows, refunded_ids)
    return _reconciliation_block(windows, scope.aggregate(**aggregates))


def reconciliation_by(scope, key, today=None):
    """{key value: reconciliation block} grouped by `key` (e.g. 'property_id'). One query."""
    windows = reconciliation_windows(today)
    aggregates = _reconciliation_aggregates(windows, fully_refunded_ids(scope))
    rows = scope.values(key).annotate(**aggregates).order_by(key)
    return {row[key]: _reconciliation_block(windows, row) for row in rows}
