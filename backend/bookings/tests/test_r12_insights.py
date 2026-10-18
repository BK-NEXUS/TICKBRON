"""
R12 additions slice 1 (.ai/PLAN_R12_ADDITIONS.md): comparison with the previous period,
cancellation rate, occupancy rate, average booking value and average stay length.
"""
from datetime import date

import pytest

from bookings import metrics
from bookings.metrics import parse_period
from bookings.tests.r12_helpers import make_booking
from bookings.tests.test_r12_metrics import TODAY, guest, hotel  # noqa: F401  (fixtures)
from properties.models import RoomType

pytestmark = pytest.mark.django_db


def insights(hotel, period, rooms=None):
    date_range = parse_period(period, today=TODAY)[1]
    scope = metrics.all_bookings().filter(property=hotel)
    totals = metrics.metric_totals(scope, date_range, today=TODAY)
    return metrics.insights(scope, date_range, totals, rooms=rooms, today=TODAY)


def add_rooms(hotel, total):
    RoomType.objects.create(property=hotel, name='Std', slug='std', base_occupancy=2, max_occupancy=2,
                            base_price=100, total_rooms=total)


class TestPreviousPeriod:

    def test_compares_with_the_period_of_the_same_length_right_before(self, hotel, guest):
        for day in (date(2026, 9, 30), date(2026, 10, 2), date(2026, 10, 4)):   # last_7_days: 3
            make_booking(hotel, guest, day, status='completed')
        make_booking(hotel, guest, date(2026, 9, 25), status='completed')       # before: 1
        result = insights(hotel, 'last_7_days')
        assert result['previous_period']['range'] == {'from': '2026-09-23', 'to': '2026-09-29'}
        assert result['previous_period']['totals']['bookings'] == 1
        assert result['change_pct']['bookings'] == '200.0'

    def test_decrease_is_negative(self, hotel, guest):
        make_booking(hotel, guest, date(2026, 10, 2), status='completed')
        for day in (date(2026, 9, 24), date(2026, 9, 25)):
            make_booking(hotel, guest, day, status='completed')
        assert insights(hotel, 'last_7_days')['change_pct']['bookings'] == '-50.0'

    def test_no_percentage_when_the_previous_period_was_empty(self, hotel, guest):
        make_booking(hotel, guest, date(2026, 10, 2), status='completed')
        assert insights(hotel, 'last_7_days')['change_pct']['bookings'] is None

    def test_all_time_has_nothing_to_compare_with(self, hotel, guest):
        make_booking(hotel, guest, date(2026, 10, 2), status='completed')
        result = insights(hotel, 'all')
        assert result['previous_period'] is None
        assert result['change_pct'] is None


class TestRates:

    def test_cancellation_rate_ignores_expired_and_pending(self, hotel, guest):
        make_booking(hotel, guest, date(2026, 10, 1), status='completed')
        make_booking(hotel, guest, date(2026, 10, 2), status='completed')
        make_booking(hotel, guest, date(2026, 10, 3), status='no_show')
        make_booking(hotel, guest, date(2026, 10, 4), status='cancelled')
        make_booking(hotel, guest, date(2026, 10, 5), status='pending')
        assert insights(hotel, 'last_7_days')['cancellation_rate'] == '25.00'   # 1 cancelled of 4 (pending left out)

    def test_cancellation_rate_is_none_without_bookings(self, hotel):
        assert insights(hotel, 'last_7_days')['cancellation_rate'] is None

    def test_occupancy_is_room_nights_over_rooms_times_days(self, hotel, guest):
        add_rooms(hotel, 5)
        make_booking(hotel, guest, date(2026, 10, 1), nights=2, rooms=2, status='completed')   # 4 room nights
        # 7 days x 5 rooms = 35 room nights
        assert insights(hotel, 'last_7_days', rooms=5)['occupancy_rate'] == '11.43'

    def test_occupancy_never_exceeds_100(self, hotel, guest):
        make_booking(hotel, guest, date(2026, 10, 6), nights=3, rooms=2, status='completed')
        assert insights(hotel, 'today', rooms=1)['occupancy_rate'] == '100.00'

    def test_occupancy_is_none_without_rooms_or_for_all_time(self, hotel, guest):
        make_booking(hotel, guest, date(2026, 10, 1), status='completed')
        assert insights(hotel, 'last_7_days', rooms=0)['occupancy_rate'] is None
        assert insights(hotel, 'all', rooms=5)['occupancy_rate'] is None


class TestAverages:

    def test_average_value_per_currency_and_stay_length(self, hotel, guest):
        make_booking(hotel, guest, date(2026, 10, 1), nights=2, status='completed', price=100)   # 200
        make_booking(hotel, guest, date(2026, 10, 3), nights=4, status='completed', price=100)   # 400
        make_booking(hotel, guest, date(2026, 10, 4), nights=1, status='completed', price=50, currency='USD')
        result = insights(hotel, 'last_7_days')
        assert result['average_booking_value'] == [
            {'currency': 'USD', 'amount': '50.00'}, {'currency': 'UZS', 'amount': '300.00'}]
        assert result['average_stay_nights'] == '2.33'

    def test_averages_are_empty_without_bookings(self, hotel):
        result = insights(hotel, 'last_7_days')
        assert result['average_booking_value'] == []
        assert result['average_stay_nights'] is None
