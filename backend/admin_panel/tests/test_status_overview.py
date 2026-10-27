"""
Admin Status overview: GET /admin-panel/status/overview/ (.ai/PLAN_STATUS_V2.md). Access: test_access_matrix.py.
Data: the status_world fixture (status_fixtures.py).
"""
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from admin_panel.tests.status_fixtures import make_booking
from bookings.models import BookingItem
from common.dates import business_today
from properties.models import RatePlan, RoomType
from users.models import User

URL = '/api/v1/admin-panel/status/overview/'

pytestmark = pytest.mark.django_db


@pytest.fixture
def get():
    staff = User.objects.create_user(email='staff@example.com', password='StaffPassword#123', is_staff=True)
    client = APIClient()
    client.force_authenticate(user=staff)
    return lambda **params: client.get(URL, params)


def money(rows):
    return {row['currency']: row['amount'] for row in rows}


def test_totals_and_insights_cover_the_whole_platform(get, status_world):
    response = get(period='2026')

    assert response.status_code == 200
    totals = response.data['totals']
    # alpha 3, beta 1, delta 1 counted in 2026; pending, cancelled, no-show and deleted ones are not
    assert (totals['bookings'], totals['guests'], totals['stayed']) == (5, 5, 1)
    assert money(totals['revenue']) == {'USD': '150.00'}
    insights = response.data['insights']
    assert insights['cancellation_rate'] == '14.29'
    assert response.data['no_show_rate'] == '14.29'
    assert {'average_lead_days', 'repeat_guest_pct'} <= set(insights)
    assert response.data['period'] == '2026'


def test_hotels_count_and_busiest_regions(get, status_world):
    data = get(period='2026').data

    assert data['hotels'] == {'total': 4, 'active': 4}
    regions = [(row['name_en'], row['bookings']) for row in data['top_regions']]
    assert regions == [('Tashkent', 4), ('Almaty City', 1), ('Unspecified', 0)]


def test_month_comparison_uses_the_platform_scope(get, status_world):
    today = business_today()
    guest = status_world['guests'][0]
    alpha = status_world['hotels']['alpha']
    make_booking(guest, alpha, today.replace(day=1), '70.00', status='completed')
    last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    make_booking(status_world['guests'][1], alpha, last_month, '30.00', status='completed')

    months = get(period='all').data['months']

    assert months['current']['bookings'] == 1
    assert money(months['current']['revenue']) == {'USD': '70.00'}
    assert months['previous']['bookings'] == 1
    assert months['change_pct']['bookings'] == '0.0'


def test_new_users_are_guests_registered_in_the_month_and_period(get, status_world):
    data = get(period='all').data

    # three guests and two owners registered just now; the staff account does not count
    assert data['new_users']['current_month'] == 5
    assert data['new_users']['previous_month'] == 0
    assert data['new_users']['in_period'] is None
    old = User.objects.get(email='guest1@example.com')
    User.objects.filter(pk=old.pk).update(date_joined=timezone.now() - timedelta(days=400))
    assert get(period='today').data['new_users']['in_period'] == 4


def test_busiest_room_types_ranked_with_their_hotel(get, status_world):
    alpha = status_world['hotels']['alpha']
    suite = RoomType.objects.create(
        property=alpha, name='Suite', slug='suite', base_occupancy=2, max_occupancy=2, base_price=Decimal('150.00'),
        currency='USD', total_rooms=2)
    plan = RatePlan.objects.create(
        room_type=suite, name='Std', slug='std-suite', rate_type='standard', base_price=Decimal('150.00'), currency='USD',
        min_nights=1, is_active=True)
    booking = make_booking(status_world['guests'][0], alpha, business_today(), '150.00', status='completed')
    BookingItem.objects.create(
        booking=booking, room_type=suite, rate_plan=plan, number_of_rooms=1, price_per_night=Decimal('150.00'), currency='USD')

    rows = get(period='all').data['top_room_types']

    assert rows[0]['name'] == 'Suite'
    assert (rows[0]['bookings'], rows[0]['property']) == (1, {'id': alpha.id, 'name': 'Alpha Hotel'})
    assert money(rows[0]['revenue']) == {'USD': '150.00'}
    assert len(rows) <= 5


def test_monthly_series_and_years(get, status_world):
    data = get(period='all', year=2026).data

    assert data['year'] == 2026
    assert data['available_years'] == [2025, 2026]
    assert len(data['monthly']) == 12
    assert next(row for row in data['monthly'] if row['month'] == '2026-04')['bookings'] == 4


@pytest.mark.parametrize('params', [{'period': 'nope'}, {'year': 'abc'}])
def test_bad_input_is_a_400(get, params):
    assert get(**params).status_code == 400


def test_new_users_are_counted_by_business_date_not_by_utc_date(get):
    # 20:00 UTC on 31 March is already 1 April 01:00 in Tashkent: it belongs to April
    late = User.objects.create_user(email='late@example.com', password='GuestPassword#123')
    User.objects.filter(pk=late.pk).update(date_joined=datetime(2026, 3, 31, 20, 0, tzinfo=dt_timezone.utc))

    assert get(period='2026-04').data['new_users']['in_period'] == 1
    assert get(period='2026-03').data['new_users']['in_period'] == 0
