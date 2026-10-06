"""
R12 phase 2: the Status definitions in bookings/metrics.py (PLAN_R12 section 1).
"""
from datetime import date, timedelta
from decimal import Decimal
from itertools import count

import pytest

from bookings import metrics
from bookings.metrics import InvalidPeriod, parse_period
from bookings.tests.r12_helpers import make_booking
from payments.models import PaymentTransaction, Refund
from properties.models import Property, PropertyType
from users.models import User

pytestmark = pytest.mark.django_db

TODAY = date(2026, 10, 6)   # a Tuesday
_keys = count(1)


def pay(booking, amount, currency='UZS', status='completed'):
    """A payment row; split or failed payments are set with update() (model validation wants one full charge)."""
    n = next(_keys)
    tx = PaymentTransaction.objects.create(
        idempotency_key=f'pay-{n}', booking=booking, provider='payme', amount=booking.charge_amount,
        currency=booking.charge_currency, status='completed', provider_transaction_id=f'ptx-{n}',
    )
    PaymentTransaction.objects.filter(pk=tx.pk).update(amount=Decimal(amount), currency=currency, status=status)
    tx.refresh_from_db()
    return tx


def refund(payment, amount, status='succeeded'):
    return Refund.objects.create(
        payment=payment, booking=payment.booking, amount=Decimal(amount), currency=payment.currency,
        reason='staff', status=status, idempotency_key=f'ref-{next(_keys)}',
    )


@pytest.fixture
def hotel():
    owner = User.objects.create_user(email='owner@example.com', password='x')
    return Property.objects.create(
        owner=owner, property_type=PropertyType.objects.create(name='Hotel', slug='hotel'),
        status='active', max_guests=8, bedrooms=1, bathrooms=1, address_line1='1', city='Tashkent',
        country='Uzbekistan', base_price=500000, currency='UZS',
    )


@pytest.fixture
def guest():
    return User.objects.create_user(email='guest@example.com', password='x')


def totals(hotel, period=None, today=TODAY):
    date_range = parse_period(period, today=today)[1] if period else None
    return metrics.metric_totals(metrics.all_bookings().filter(property=hotel), date_range, today=today)


def money(rows):
    return {row['currency']: row['amount'] for row in rows}


class TestPeriods:

    @pytest.mark.parametrize('period, first, last', [
        ('today', date(2026, 10, 6), date(2026, 10, 6)),
        ('last_7_days', date(2026, 9, 30), date(2026, 10, 6)),
        ('last_30_days', date(2026, 9, 7), date(2026, 10, 6)),
        ('this_year', date(2026, 1, 1), date(2026, 12, 31)),
        ('last_5_years', date(2021, 10, 7), date(2026, 10, 6)),
        ('last_10_years', date(2016, 10, 7), date(2026, 10, 6)),
        ('2025', date(2025, 1, 1), date(2025, 12, 31)),
        ('2026-02', date(2026, 2, 1), date(2026, 2, 28)),
    ])
    def test_named_periods(self, period, first, last):
        label, (start, after) = parse_period(period, today=TODAY)
        assert label == period
        assert (start, after - timedelta(days=1)) == (first, last)

    def test_all(self):
        assert parse_period('all', today=TODAY) == ('all', None)
        assert parse_period(None, today=TODAY) == ('all', None)

    def test_leap_day_years_back(self):
        _, (start, _) = parse_period('last_5_years', today=date(2028, 2, 29))
        assert start == date(2023, 3, 1)

    def test_custom(self):
        label, (start, after) = parse_period('custom', '2026-01-10', '2026-01-20', today=TODAY)
        assert (label, start, after) == ('custom', date(2026, 1, 10), date(2026, 1, 21))
        assert parse_period('custom', '2026-01-10', '2026-01-10', today=TODAY)[1] == \
            (date(2026, 1, 10), date(2026, 1, 11))
        assert parse_period('custom', '2006-01-02', '2026-01-01', today=TODAY)[1][0] == date(2006, 1, 2)

    @pytest.mark.parametrize('date_from, date_to', [
        ('2026-01-20', '2026-01-10'),       # from after to
        ('2006-01-01', '2026-01-01'),       # more than 20 years
        ('2026-13-01', '2026-01-10'),       # bad date
        ('yesterday', '2026-01-10'),
        (None, '2026-01-10'),
        ('2026-01-10', None),
    ])
    def test_custom_invalid(self, date_from, date_to):
        with pytest.raises(InvalidPeriod):
            parse_period('custom', date_from, date_to, today=TODAY)

    @pytest.mark.parametrize('period', ['last_8_days', '2026-13', '1999', 'soon', '26'])
    def test_invalid(self, period):
        with pytest.raises(InvalidPeriod):
            parse_period(period, today=TODAY)


class TestBuckets:

    def test_week_buckets_start_on_monday(self):
        starts = metrics.buckets((date(2026, 10, 1), date(2026, 10, 15)), 'week')
        assert starts == [date(2026, 9, 28), date(2026, 10, 5), date(2026, 10, 12)]

    def test_bucket_cap(self):
        assert len(metrics.buckets((date(2024, 1, 1), date(2026, 9, 27)), 'day')) == 1000
        with pytest.raises(InvalidPeriod):
            metrics.buckets((date(2016, 10, 7), date(2026, 10, 7)), 'day')
        assert len(metrics.buckets((date(2016, 10, 7), date(2026, 10, 7)), 'month')) == 121

    @pytest.mark.parametrize('value', ['hour', 'quarter', 'Month'])
    def test_unknown_granularity(self, value):
        with pytest.raises(InvalidPeriod):
            metrics.parse_granularity(value)


class TestCounting:

    def test_persons_vs_unique_customers_nights_and_room_nights(self, hotel, guest):
        day = TODAY - timedelta(days=20)
        make_booking(hotel, guest, day, nights=2, guest_count=2, status='completed')
        make_booking(hotel, guest, day + timedelta(days=3), nights=3, guest_count=4, rooms=2, status='completed')
        make_booking(hotel, guest, day + timedelta(days=7), nights=1, guest_count=4)
        t = totals(hotel)
        assert (t['bookings'], t['guests'], t['unique_customers']) == (3, 10, 1)
        assert (t['nights'], t['room_nights']) == (6, 2 + 6 + 1)
        assert (t['stayed'], t['counted']) == (2, 3)

    def test_cancelled_pending_and_expired_never_count(self, hotel, guest):
        day = TODAY - timedelta(days=10)
        make_booking(hotel, guest, day, status='pending')
        make_booking(hotel, guest, day, status='cancelled')
        expired = make_booking(hotel, guest, day, status='cancelled')
        expired.cancellation_reason = metrics.EXPIRY_REASON
        expired.save(update_fields=['cancellation_reason'])
        make_booking(hotel, guest, day, status='no_show')
        t = totals(hotel)
        assert (t['bookings'], t['guests'], t['nights'], t['stayed']) == (0, 0, 0, 0)
        assert t['booking_status'] == {
            'pending': 1, 'confirmed': 0, 'completed': 0, 'cancelled': 1, 'expired': 1,
            'no_show': 1, 'no_show_reported': 0,
        }
        assert (t['no_show'], t['no_show_reported']) == (1, 0)

    def test_period_uses_the_check_in_date(self, hotel, guest):
        make_booking(hotel, guest, TODAY - timedelta(days=6), status='completed')
        make_booking(hotel, guest, TODAY - timedelta(days=7), status='completed')
        assert totals(hotel, 'last_7_days')['bookings'] == 1
        assert totals(hotel, 'last_30_days')['bookings'] == 2

    def test_upcoming_is_not_limited_by_the_period(self, hotel, guest):
        make_booking(hotel, guest, TODAY + timedelta(days=1))
        make_booking(hotel, guest, TODAY + timedelta(days=400))
        make_booking(hotel, guest, TODAY)                       # today is not "after today"
        make_booking(hotel, guest, TODAY + timedelta(days=5), status='pending')
        t = totals(hotel, 'last_7_days')
        assert t['upcoming'] == 2
        assert t['bookings'] == 1                                # only today's check-in is in the period

    def test_soft_deleted_bookings_never_count(self, hotel, guest):
        b = make_booking(hotel, guest, TODAY - timedelta(days=3), status='completed')
        pay(b, '1000000')
        b.is_deleted = True
        b.save(update_fields=['is_deleted'])
        t = totals(hotel)
        assert (t['bookings'], t['revenue'], t['booking_status']['completed']) == (0, [], 0)


class TestRefundRule:

    def test_full_refund_over_two_payments_is_excluded(self, hotel, guest):
        b = make_booking(hotel, guest, TODAY - timedelta(days=10), status='completed', guest_count=3)
        refund(pay(b, '600000'), '600000')
        refund(pay(b, '400000'), '400000')
        t = totals(hotel)
        assert (t['bookings'], t['guests'], t['nights'], t['stayed'], t['revenue']) == (0, 0, 0, 0, [])
        assert t['fully_refunded'] == 1
        assert t['booking_value'] == []

    def test_partial_refund_stays_counted_with_paid_minus_refunded(self, hotel, guest):
        b = make_booking(hotel, guest, TODAY - timedelta(days=10), status='completed')
        p = pay(b, '1000000')
        refund(p, '300000')
        refund(p, '100000')
        t = totals(hotel)
        assert (t['bookings'], t['fully_refunded']) == (1, 0)
        assert money(t['revenue']) == {'UZS': '600000.00'}

    def test_one_payment_refunded_the_other_not_stays_counted(self, hotel, guest):
        b = make_booking(hotel, guest, TODAY - timedelta(days=10), status='completed')
        refund(pay(b, '600000'), '600000')
        pay(b, '400000')
        t = totals(hotel)
        assert (t['bookings'], t['fully_refunded']) == (1, 0)
        assert money(t['revenue']) == {'UZS': '400000.00'}

    @pytest.mark.parametrize('status', ['failed', 'pending', 'needs_manual'])
    def test_refunds_that_did_not_succeed_are_ignored(self, hotel, guest, status):
        b = make_booking(hotel, guest, TODAY - timedelta(days=10), status='completed')
        refund(pay(b, '1000000'), '1000000', status=status)
        t = totals(hotel)
        assert (t['bookings'], t['fully_refunded']) == (1, 0)
        assert money(t['revenue']) == {'UZS': '1000000.00'}

    def test_currencies_are_never_mixed(self, hotel, guest):
        b1 = make_booking(hotel, guest, TODAY - timedelta(days=10), status='completed')
        b2 = make_booking(hotel, guest, TODAY - timedelta(days=9), status='completed', currency='USD',
                          price=Decimal('50'))
        pay(b1, '1000000')
        p = pay(b2, '100.00', currency='USD')
        refund(p, '30.00')
        assert money(totals(hotel)['revenue']) == {'UZS': '1000000.00', 'USD': '70.00'}
        assert money(totals(hotel)['booking_value']) == {'UZS': '1000000.00', 'USD': '100.00'}

    def test_unpaid_or_failed_payments_are_not_revenue(self, hotel, guest):
        b = make_booking(hotel, guest, TODAY - timedelta(days=10), status='completed')
        pay(b, '1000000', status='failed')
        pay(b, '1000000', status='pending')
        t = totals(hotel)
        assert (t['bookings'], t['revenue'], t['fully_refunded']) == (1, [], 0)

    def test_booking_without_payments_counts_with_revenue_zero(self, hotel, guest):
        make_booking(hotel, guest, TODAY - timedelta(days=10), status='completed')
        t = totals(hotel)
        assert (t['bookings'], t['revenue'], t['fully_refunded']) == (1, [], 0)
        assert money(t['booking_value']) == {'UZS': '1000000.00'}

    def test_no_show_keeps_the_money_not_refunded(self, hotel, guest):
        b = make_booking(hotel, guest, TODAY - timedelta(days=10), status='no_show')
        refund(pay(b, '1000000'), '500000')
        t = totals(hotel)
        assert (t['bookings'], t['no_show'], t['fully_refunded']) == (0, 1, 0)
        assert money(t['revenue']) == {'UZS': '500000.00'}

    def test_fully_refunded_no_show_is_only_in_fully_refunded(self, hotel, guest):
        b = make_booking(hotel, guest, TODAY - timedelta(days=10), status='no_show')
        refund(pay(b, '1000000'), '1000000')
        t = totals(hotel)
        assert (t['no_show'], t['fully_refunded'], t['revenue']) == (0, 1, [])

    def test_cancelled_refunded_booking_is_not_fully_refunded_count(self, hotel, guest):
        b = make_booking(hotel, guest, TODAY - timedelta(days=10), status='cancelled')
        refund(pay(b, '1000000'), '1000000')
        t = totals(hotel)
        assert (t['fully_refunded'], t['revenue']) == (0, [])


class TestSeries:

    def test_empty_buckets_are_included(self, hotel, guest):
        b = make_booking(hotel, guest, date(2026, 9, 29), status='completed', guest_count=2)
        pay(b, '1000000')
        make_booking(hotel, guest, date(2026, 10, 1), status='completed')
        rows = metrics.series(metrics.all_bookings().filter(property=hotel),
                              (date(2026, 9, 28), date(2026, 10, 12)), 'week', today=TODAY)
        assert [(r['period'], r['bookings'], r['guests'], r['stayed']) for r in rows] == [
            ('2026-09-28', 2, 3, 2), ('2026-10-05', 0, 0, 0),
        ]
        assert money(rows[0]['revenue']) == {'UZS': '1000000.00'} and rows[1]['revenue'] == []

    def test_day_month_year_labels(self, hotel, guest):
        make_booking(hotel, guest, date(2026, 2, 3), status='completed')
        scope = metrics.all_bookings().filter(property=hotel)
        assert [r['period'] for r in metrics.series(scope, (date(2026, 2, 2), date(2026, 2, 4)), 'day')] == \
            ['2026-02-02', '2026-02-03']
        months = metrics.series(scope, (date(2026, 1, 1), date(2027, 1, 1)), 'month')
        assert len(months) == 12 and months[1] == {**months[1], 'period': '2026-02', 'bookings': 1}
        assert [r['period'] for r in metrics.series(scope, (date(2025, 1, 1), date(2027, 1, 1)), 'year')] == \
            ['2025', '2026']

    def test_all_time_runs_from_the_first_check_in_to_today(self, hotel, guest):
        make_booking(hotel, guest, date(2026, 8, 15), status='completed')
        rows = metrics.series(metrics.all_bookings().filter(property=hotel), None, 'month', today=TODAY)
        assert [r['period'] for r in rows] == ['2026-08', '2026-09', '2026-10']
        assert metrics.series(metrics.all_bookings().filter(property=hotel, guest__isnull=True), None, 'month') == []


class TestReconciliation:

    def test_windows(self, hotel, guest):
        make_booking(hotel, guest, TODAY, guest_count=2)                                   # today
        make_booking(hotel, guest, TODAY - timedelta(days=1), status='completed')           # Monday
        make_booking(hotel, guest, date(2026, 10, 2), status='completed', guest_count=3)    # this month
        make_booking(hotel, guest, date(2026, 3, 2), status='completed')                    # this year
        make_booking(hotel, guest, date(2025, 3, 2), status='completed')                    # earlier
        make_booking(hotel, guest, TODAY, status='cancelled')
        r = metrics.reconciliation(metrics.all_bookings().filter(property=hotel), today=TODAY)
        assert (r['today']['from'], r['today']['to']) == ('2026-10-06', '2026-10-06')
        assert (r['this_week']['from'], r['this_week']['to']) == ('2026-10-05', '2026-10-11')
        assert (r['all_time']['from'], r['all_time']['to']) == (None, None)
        summary = {name: (w['counted']['bookings'], w['counted']['guests'], w['stayed']['bookings'],
                          w['stayed']['guests']) for name, w in r.items()}
        assert summary == {
            'today': (1, 2, 0, 0),
            'this_week': (2, 3, 1, 1),
            'this_month': (3, 6, 2, 4),
            'this_year': (4, 7, 3, 5),
            'all_time': (5, 8, 4, 6),
        }
