"""
Status definitions (R12 phase 2, .ai/PLAN_R12.md section 1). The one place that says what
a guest, a stay, a night and revenue are; bookings/stats.py keeps its old public names as
thin wrappers, and every Status view (admin and partner) reads these functions.

- Date basis: the CHECK-IN date. "Today" = common.dates.business_today() (Asia/Tashkent).
- counted   = confirmed + completed, not soft-deleted.
- stayed    = completed (the headline number).
- upcoming  = confirmed with check-in after today; never limited by the period.
- bookings  = COUNT of counted bookings.
- every headline number also exists as PERSONS (SUM(guest_count)): counted_guests (= guests),
              stayed_guests (completed) and upcoming_guests (upcoming); the reconciliation blocks
              carry bookings and guests for counted and stayed.
- guests    = SUM(guest_count) of counted bookings (persons; guest_count includes children).
- unique_customers = COUNT(DISTINCT guest) of counted bookings (the old `guests`).
- nights    = SUM(number_of_nights); room_nights = SUM(number_of_nights x number_of_rooms).
- no_show   = status no_show (an approved report); no_show_reported = has a
              pending no-show report. A reported booking is neither stayed nor no_show until staff
              decide: it is left out of the confirmed / completed counts of booking_status.
- revenue   = cash expected at the hotel (plan .ai/PLAN_CASH_ONLY.md: there are no online payments): per
              currency, never mixed, SUM(total_price) of COMPLETED bookings. A confirmed booking is not revenue
              until the stay is completed; cancelled, expired and no-show bookings are never revenue.
- booking_value = SUM(total_price) of counted bookings (confirmed + completed) in the hotel's currency.
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
from decimal import Decimal

from django.conf import settings
from django.db.models import Avg, Count, DurationField, Exists, ExpressionWrapper, F, IntegerField, Max, Min, OuterRef, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDate, TruncDay, TruncMonth, TruncWeek, TruncYear

from common.dates import business_time_zone, business_today

COUNTED_STATUSES = ('confirmed', 'completed')
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
    period = (params.get('period') or '').strip()
    if (params.get('from') or params.get('to')) and period != 'custom':
        raise InvalidPeriod('from and to are used only with period=custom.')
    return parse_period(period, params.get('from'), params.get('to'))


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


# --- booking sets -------------------------------------------------------------------

def period_q(prefix='', date_range=None):
    if not date_range:
        return Q()
    first, after = date_range
    return Q(**{f'{prefix}check_in__gte': first, f'{prefix}check_in__lt': after})


def counted_q(prefix='', date_range=None):
    """Q for counted bookings; `prefix` is the path to Booking, e.g. 'bookings__'."""
    return Q(**{f'{prefix}status__in': COUNTED_STATUSES, f'{prefix}is_deleted': False}) & period_q(prefix, date_range)


def revenue_q(prefix='', date_range=None):
    """Bookings whose money is revenue: the stay is completed (the cash was handed over at the hotel)."""
    return Q(**{f'{prefix}status': 'completed', f'{prefix}is_deleted': False}) & period_q(prefix, date_range)


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
    """Confirmed bookings checking in after today; never limited by a period."""
    today = today or business_today()
    return Q(**{f'{prefix}status': 'confirmed', f'{prefix}is_deleted': False, f'{prefix}check_in__gt': today})


def guest_annotations(prefix='bookings__', date_range=None, today=None):
    """Persons (SUM guest_count) of counted, stayed and upcoming bookings, for .annotate()."""
    counted = counted_q(prefix, date_range)
    return {
        'counted_guests_count': Coalesce(Sum(f'{prefix}guest_count', filter=counted), 0),
        'stayed_guests_count': Coalesce(
            Sum(f'{prefix}guest_count', filter=counted & Q(**{f'{prefix}status': 'completed'})), 0),
        'upcoming_guests_count': Coalesce(Sum(f'{prefix}guest_count', filter=upcoming_q(prefix, today)), 0),
    }


def metric_annotations(prefix='bookings__', date_range=None, today=None):
    """
    Counted bookings, guests, unique customers, nights, room nights and stays, for .annotate().
    """
    counted = counted_q(prefix, date_range)
    return {
        'bookings_count': Count(f'{prefix}id', filter=counted, distinct=True),
        'guests_count': Coalesce(Sum(f'{prefix}guest_count', filter=counted), 0),
        'unique_customers_count': Count(f'{prefix}guest', filter=counted, distinct=True),
        'nights_count': Coalesce(Sum(f'{prefix}number_of_nights', filter=counted), 0),
        'room_nights_count': Coalesce(
            Sum(F(f'{prefix}number_of_nights') * F(f'{prefix}number_of_rooms'), filter=counted,
                output_field=IntegerField()), 0),
        'stayed_count': Count(f'{prefix}id', filter=counted & Q(**{f'{prefix}status': 'completed'}), distinct=True),
        **guest_annotations(prefix, date_range, today),
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
    {key value: [{'currency', 'amount'}, ...]}: SUM(total_price) per booking currency, for already-filtered
    revenue bookings (completed stays). `key` is a Booking lookup or annotation.
    """
    return booking_value_by(bookings, key)


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


def metric_totals(scope, date_range=None, today=None):
    """
    Every number of section 1 for the bookings in `scope` (a not-deleted Booking queryset
    narrowed to a hotel, an owner or a guest; NOT narrowed to the period). One aggregate
    query for the counts plus two for revenue and one for booking value.
    """
    today = today or business_today()
    counted = counted_q('', date_range)
    in_period = period_q('', date_range)
    upcoming = Q(status='confirmed', check_in__gt=today)
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
        no_show=Count('id', filter=in_period & Q(status='no_show')),
        **_status_counts(date_range),
    )
    in_revenue = scope.filter(revenue_q('', date_range))
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


# --- insights (R12 additions) ---------------------------------------------------------

def previous_range(date_range):
    """The period of the same length right before `date_range`; None for all time."""
    if date_range is None:
        return None
    first, after = date_range
    return first - (after - first), first


def _percent(part, whole):
    return f'{Decimal(part) * 100 / Decimal(whole):.2f}' if whole else None


def _change_pct(current, previous):
    """Change in percent with one decimal ('-50.0'); None when there is nothing to compare with."""
    return f'{(Decimal(current) - Decimal(previous)) * 100 / Decimal(previous):.1f}' if previous else None


def _revenue_change(current, previous):
    before = {row['currency']: Decimal(row['amount']) for row in previous}
    return [{'currency': row['currency'], 'pct': _change_pct(row['amount'], before.get(row['currency'], 0))}
            for row in current]


def _average_values(bookings):
    rows = (bookings.values('currency').annotate(amount=Sum('total_price'), count=Count('id')).order_by('currency'))
    return [{'currency': row['currency'], 'amount': _money(row['amount'] / row['count'])} for row in rows]


def rooms_offered(properties):
    """Rooms the given hotels (a Property queryset) offer: SUM(total_rooms) of their room types."""
    from properties.models import RoomType
    return RoomType.objects.filter(property__in=properties, is_deleted=False).aggregate(
        total=Coalesce(Sum('total_rooms'), 0))['total']


RANK_MIN_HOTELS = 5   # below this a rank would let owners guess who is who


def region_rank(prop, date_range):
    """
    {'position', 'of'}: the hotel's place among the active hotels of its region by counted
    bookings in the period (equal numbers share a place). Only the hotel's own place and the
    number of hotels leave this function. None without a region, when the hotel is not active
    or when the region has fewer than RANK_MIN_HOTELS active hotels.
    """
    from properties.models import Property
    if not prop.region_ref_id:
        return None
    peers = Property.objects.filter(region_ref_id=prop.region_ref_id, status='active', is_deleted=False)
    peer_ids = list(peers.values_list('id', flat=True))
    if len(peer_ids) < RANK_MIN_HOTELS or prop.id not in peer_ids:
        return None
    scope = all_bookings().filter(property_id__in=peer_ids)
    counts = dict(scope.filter(counted_q('', date_range))
                  .values_list('property_id').annotate(total=Count('id')).order_by())
    own = counts.get(prop.id, 0)
    return {'position': 1 + sum(1 for total in counts.values() if total > own), 'of': len(peer_ids)}


def average_lead_days(bookings):
    """Days between the day a booking was made (business date) and its check-in, on average; None without bookings."""
    lead = ExpressionWrapper(F('check_in') - TruncDate('created_at', tzinfo=business_time_zone()), output_field=DurationField())
    average = bookings.aggregate(days=Avg(lead))['days']
    return f'{average.total_seconds() / 86400:.1f}' if average is not None else None


def repeat_guest_pct(bookings, unique_customers):
    """Share of the guests (accounts) with more than one of these bookings, in percent; None without guests."""
    repeat = bookings.values('guest').annotate(n=Count('id')).filter(n__gt=1).count()
    return _percent(repeat, unique_customers)


def month_comparison(scope, today=None):
    """
    This calendar month against the last one (whatever period the page shows) and the guests arriving in the next
    7 days (today included): {'current', 'previous'} with the month, its range, bookings, guests and revenue,
    'change_pct' and 'next_7_days' {'bookings', 'guests'} (confirmed bookings).
    """
    today = today or business_today()
    this_first = today.replace(day=1)
    next_first = _next_month(this_first)
    last_first = _previous_month(this_first)
    blocks = {}
    for key, first, after in (('current', this_first, next_first), ('previous', last_first, this_first)):
        totals = metric_totals(scope, (first, after), today)
        blocks[key] = {'month': first.strftime('%Y-%m'), 'range': range_json((first, after)), 'bookings': totals['bookings'],
                       'guests': totals['guests'], 'revenue': totals['revenue']}
    soon = scope.filter(status='confirmed', check_in__gte=today, check_in__lt=today + timedelta(days=7)).aggregate(
        bookings=Count('id'), guests=Coalesce(Sum('guest_count'), 0))
    return {
        **blocks,
        'change_pct': {
            'bookings': _change_pct(blocks['current']['bookings'], blocks['previous']['bookings']),
            'guests': _change_pct(blocks['current']['guests'], blocks['previous']['guests']),
            'revenue': _revenue_change(blocks['current']['revenue'], blocks['previous']['revenue']),
        },
        'next_7_days': soon,
    }


def _next_month(first):
    return (first.replace(day=28) + timedelta(days=4)).replace(day=1)


def _previous_month(first):
    return (first - timedelta(days=1)).replace(day=1)


def room_type_stats(scope, date_range, room_types):
    """
    One row per room type of `room_types` (a RoomType queryset; types nobody booked are listed with zeros),
    busiest first: counted bookings that include it, room nights (rooms x nights by check-in date), revenue per currency
    (its items of completed stays: price per night x rooms x nights), its share of all the counted room-type bookings
    in percent, and the occupancy rate over a bounded period (room nights / rooms offered x days; None for all time).
    `scope` is a Booking queryset (not narrowed to the period).
    """
    from bookings.models import BookingItem
    items = BookingItem.objects.filter(is_deleted=False, room_type__in=room_types)
    counted = items.filter(booking__in=scope.filter(counted_q('', date_range)))
    nights = F('number_of_rooms') * F('booking__number_of_nights')
    stats = {
        row['room_type_id']: row for row in counted.values('room_type_id').annotate(
            bookings=Count('booking', distinct=True), room_nights=Coalesce(Sum(nights, output_field=IntegerField()), 0))
    }
    money = {}
    revenue_items = items.filter(booking__in=scope.filter(revenue_q('', date_range)))
    for row in revenue_items.values('room_type_id', 'currency').annotate(
            amount=Sum(F('price_per_night') * nights)).order_by('room_type_id', 'currency'):
        money.setdefault(row['room_type_id'], []).append({'currency': row['currency'], 'amount': _money(row['amount'])})
    total_bookings = sum(row['bookings'] for row in stats.values())
    days = (date_range[1] - date_range[0]).days if date_range else None
    rows = []
    for kind in room_types.order_by('id'):
        row = stats.get(kind.id, {'bookings': 0, 'room_nights': 0})
        offered = kind.total_rooms * days if days and kind.total_rooms else 0
        rows.append({
            'room_type_id': kind.id, 'name': kind.name, 'property_id': kind.property_id, 'total_rooms': kind.total_rooms,
            'bookings': row['bookings'], 'room_nights': row['room_nights'], 'revenue': money.get(kind.id, []),
            'share_pct': _percent(row['bookings'], total_bookings),
            'occupancy_rate': _percent(min(row['room_nights'], offered), offered) if offered else None,
        })
    return sorted(rows, key=lambda row: (-row['bookings'], -row['room_nights'], row['name'], row['room_type_id']))


def insights(scope, date_range, totals, rooms=None, today=None):
    """
    Derived numbers of the Status pages for the bookings in `scope`, from their `totals`
    (metric_totals of the same scope and range): the previous period and the
    change in percent, cancellation rate, occupancy rate (needs `rooms`, the number of rooms the
    hotels offer; room nights are by check-in date), average booking value per currency and
    average stay length. Read only; every rate is None when its denominator is 0.
    """
    today = today or business_today()
    status = totals['booking_status']
    result = {
        'cancellation_rate': _percent(status['cancelled'], status['cancelled'] + totals['bookings'] + totals['no_show']),
        'average_booking_value': _average_values(scope.filter(counted_q('', date_range))),
        'average_stay_nights': (f"{Decimal(totals['nights']) / totals['bookings']:.2f}" if totals['bookings'] else None),
        'occupancy_rate': None,
        'average_lead_days': average_lead_days(scope.filter(counted_q('', date_range))),
        'repeat_guest_pct': repeat_guest_pct(scope.filter(counted_q('', date_range)), totals['unique_customers']),
        'previous_period': None,
        'change_pct': None,
    }
    if date_range is None:
        return result
    days = (date_range[1] - date_range[0]).days
    if rooms:
        result['occupancy_rate'] = _percent(min(totals['room_nights'], rooms * days), rooms * days)
    before = previous_range(date_range)
    previous = metric_totals(scope, before, today)
    keys = ('bookings', 'guests', 'nights', 'stayed')
    result['previous_period'] = {
        'range': range_json(before),
        'totals': {key: previous[key] for key in keys} | {'revenue': previous['revenue']},
    }
    result['change_pct'] = {key: _change_pct(totals[key], previous[key]) for key in keys} | {
        'revenue': _revenue_change(totals['revenue'], previous['revenue'])}
    return result


# --- series -------------------------------------------------------------------------

def series(scope, date_range, granularity, today=None):
    """
    One row per bucket ({'period', 'start', 'bookings', 'guests', 'nights', 'stayed',
    'revenue'}), empty buckets included. With date_range None the range runs from the first
    check-in of `scope` to today (or the last check-in when later). InvalidPeriod above
    MAX_BUCKETS buckets.
    """
    today = today or business_today()
    if date_range is None:
        span = scope.filter(counted_q('', None)).aggregate(first=Min('check_in'), last=Max('check_in'))
        if span['first'] is None:
            return []
        date_range = (span['first'], max(span['last'], today) + timedelta(days=1))
    starts = buckets(date_range, granularity)
    trunc = _TRUNC[granularity]('check_in')
    counted = scope.filter(counted_q('', date_range)).annotate(bucket=trunc)
    counts = {
        _as_date(row['bucket']): row
        for row in counted.values('bucket').annotate(
            n=Count('id'), g=Coalesce(Sum('guest_count'), 0), nights=Coalesce(Sum('number_of_nights'), 0),
            stayed=Count('id', filter=Q(status='completed')),
        ).order_by('bucket')
    }
    money = revenue_by(scope.filter(revenue_q('', date_range)).annotate(bucket=trunc), 'bucket')
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


def monthly_series(scope, year):
    """
    Twelve rows for `year` ({'month': 'YYYY-MM', 'bookings', 'guests', 'revenue'}), kept for
    the existing `monthly` field. `scope` is a not-deleted Booking queryset.
    """
    rows = series(scope, (date(year, 1, 1), date(year + 1, 1, 1)), 'month')
    return [{'month': row['period'], 'bookings': row['bookings'], 'guests': row['guests'],
             'nights': row['nights'], 'stayed': row['stayed'], 'revenue': row['revenue']} for row in rows]


def available_years(scope):
    """Years (ascending) that have at least one counted booking, for the year selector."""
    return [day.year for day in scope.filter(counted_q('', None)).dates('check_in', 'year')]


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


def _reconciliation_aggregates(windows):
    aggregates = {}
    for name, window in windows.items():
        counted = counted_q('', window)
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


def reconciliation(scope, today=None):
    """
    {window: {'from', 'to', 'counted': {bookings, guests}, 'stayed': {bookings, guests}}}
    for today, this week (Mon-Sun), this month, this year and all time. One query.
    """
    windows = reconciliation_windows(today)
    aggregates = _reconciliation_aggregates(windows)
    return _reconciliation_block(windows, scope.aggregate(**aggregates))


def reconciliation_by(scope, key, today=None):
    """{key value: reconciliation block} grouped by `key` (e.g. 'property_id'). One query."""
    windows = reconciliation_windows(today)
    aggregates = _reconciliation_aggregates(windows)
    rows = scope.values(key).annotate(**aggregates).order_by(key)
    return {row[key]: _reconciliation_block(windows, row) for row in rows}
