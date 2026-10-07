"""
R12a-fix: the Status numbers exist as bookings AND as persons.

stayed_guests / counted_guests / upcoming_guests next to stayed / counted / upcoming, on every
statistics endpoint (admin and owner), plus `business_date` and `no_show_report_window_days`
in the response meta.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest import mock

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from admin_panel.tests.status_fixtures import make_booking
from bookings.metrics import status_meta
from bookings.models import Booking
from common.dates import business_today
from payments.models import PaymentTransaction, Refund
from users.models import User

S = '/api/v1/admin-panel/status'
P = '/api/v1/partner/status'
PERSON_FIELDS = ('counted_guests', 'stayed_guests', 'upcoming_guests')


@pytest.fixture
def staff(db):
    return User.objects.create_user(email='staff@example.com', password='StaffPassword#123', is_staff=True)


@pytest.fixture
def get(staff):
    client = APIClient()
    client.force_authenticate(user=staff)
    return lambda url, **params: client.get(url, params)


def persons(booking, count):
    Booking.objects.filter(pk=booking.pk).update(guest_count=count)
    return booking


@pytest.fixture
def people(status_world):
    """
    Hotel Beta. status_world already gives it one completed (1 person) and one confirmed (1 person)
    booking; these add 4 + 3 persons completed, 2 + 5 confirmed (the last one in the future), 7 cancelled.
    """
    beta, guest = status_world['hotels']['beta'], status_world['guests'][0]
    today = business_today()
    persons(make_booking(guest, beta, today - timedelta(days=20), '10.00', status='completed'), 4)
    persons(make_booking(guest, beta, today - timedelta(days=15), '10.00', status='completed'), 3)
    persons(make_booking(guest, beta, today - timedelta(days=3), '10.00', status='confirmed'), 2)
    persons(make_booking(guest, beta, today + timedelta(days=5), '10.00', status='confirmed'), 5)
    persons(make_booking(guest, beta, today - timedelta(days=9), '10.00', status='cancelled'), 7)
    return beta


def beta_totals(get, beta):
    return get(f'{S}/hotels/{beta.id}/', period='all').data['totals']


@pytest.mark.django_db
class TestPersonsAreNotBookings:

    def test_stayed_guests_sums_persons_of_completed_bookings(self, get, people):
        totals = beta_totals(get, people)
        assert (totals['stayed'], totals['stayed_guests']) == (3, 8)

    def test_counted_and_upcoming_guests(self, get, people):
        totals = beta_totals(get, people)
        # confirmed + completed, all time: 2 from the fixture + 4 + 3 + 2 + the future one (5)
        assert totals['counted_guests'] == totals['guests'] == 16
        assert (totals['upcoming'], totals['upcoming_guests']) == (1, 5)

    def test_cancelled_is_not_counted_anywhere(self, get, people):
        totals = beta_totals(get, people)
        assert totals['counted_guests'] == 16 and totals['stayed_guests'] == 8

    def test_fully_refunded_is_excluded(self, get, people):
        refunded = Booking.objects.filter(property=people, status='completed', guest_count=4).get()
        payment = PaymentTransaction.objects.get(booking=refunded)
        Refund.objects.create(payment=payment, booking=refunded, amount=payment.amount, currency=payment.currency,
                              reason='staff', status='succeeded', idempotency_key='fix-full')
        totals = beta_totals(get, people)
        assert (totals['stayed'], totals['stayed_guests'], totals['counted_guests']) == (2, 4, 12)

    def test_a_partial_refund_still_counts(self, get, people):
        booking = Booking.objects.filter(property=people, status='completed', guest_count=4).get()
        payment = PaymentTransaction.objects.get(booking=booking)
        Refund.objects.create(payment=payment, booking=booking, amount=payment.amount / 2, currency=payment.currency,
                              reason='no_show', status='succeeded', idempotency_key='fix-half')
        assert beta_totals(get, people)['stayed_guests'] == 8

    def test_period_limits_stayed_but_not_upcoming(self, get, people):
        totals = get(f'{S}/hotels/{people.id}/', period='today').data['totals']
        assert (totals['stayed_guests'], totals['upcoming_guests']) == (0, 5)

    def test_hotel_row_in_the_lists(self, get, people):
        row = next(r for r in get(f'{S}/hotels/', period='all', page_size=100).data['results']
                   if r['id'] == people.id)
        assert (row['counted_guests'], row['stayed_guests'], row['upcoming_guests']) == (16, 8, 5)
        assert row['guests'] == row['counted_guests']


@pytest.mark.django_db
class TestConsistency:

    @pytest.mark.parametrize('period', ['all', 'last_30_days', '2026', '2025'])
    def test_stayed_guests_over_users_equals_over_hotels(self, get, status_world, people, period):
        hotels = get(f'{S}/hotels/', period=period, page_size=100).data['results']
        users = get(f'{S}/users/', period=period, page_size=100).data['results']
        for field in PERSON_FIELDS[:2]:
            assert sum(r[field] for r in hotels) == sum(r[field] for r in users), field

    def test_user_per_hotel_row_matches_the_database(self, get, status_world, people):
        guest = status_world['guests'][0]
        row = next(r for r in get(f'{S}/users/{guest.id}/').data['hotels'] if r['id'] == people.id)
        completed = Booking.objects.filter(guest=guest, property=people, status='completed')
        assert row['stayed_guests'] == sum(b.guest_count for b in completed) == 7
        assert row['counted_guests'] == row['guests']

    def test_user_totals_have_the_fields(self, get, status_world, people):
        guest = status_world['guests'][0]
        totals = get(f'{S}/users/{guest.id}/', period='last_30_days').data['totals']
        assert (totals['stayed_guests'], totals['upcoming_guests']) == (7, 5)

    def test_reconciliation_already_carries_persons(self, get, people):
        block = get(f'{S}/hotels/{people.id}/').data['reconciliation']['all_time']
        assert block['stayed']['guests'] == 8 and block['counted']['guests'] == 16


@pytest.mark.django_db
class TestFieldsOnEveryEndpoint:

    def urls(self, status_world):
        alpha = status_world['hotels']['alpha']
        user = status_world['guests'][0]
        region = alpha.region_ref_id
        return {
            'countries': f'{S}/countries/', 'regions': f'{S}/countries/UZ/regions/',
            'region_hotels': f'{S}/countries/UZ/regions/{region}/hotels/', 'hotels': f'{S}/hotels/',
            'hotel_detail': f'{S}/hotels/{alpha.id}/', 'users': f'{S}/users/', 'user_detail': f'{S}/users/{user.id}/',
        }

    def test_admin_rows_and_totals(self, get, status_world):
        for name, url in self.urls(status_world).items():
            data = get(url).data
            assert data['business_date'] == business_today().isoformat(), name
            assert data['no_show_report_window_days'] == 7, name
            if 'totals' in data:
                assert all(field in data['totals'] for field in PERSON_FIELDS), name
            for row in data.get('results', []):
                assert all(field in row for field in PERSON_FIELDS), name
            for row in data.get('hotels', []):
                assert 'stayed_guests' in row and 'counted_guests' in row, name

    def test_owner_endpoints(self, status_world):
        owner = status_world['owners'][0]
        client = APIClient()
        client.force_authenticate(user=owner)
        alpha = status_world['hotels']['alpha']
        summary = client.get(f'{P}/').data
        detail = client.get(f'{P}/hotels/{alpha.id}/').data
        for data in (summary, detail):
            assert data['business_date'] == business_today().isoformat()
            assert data['no_show_report_window_days'] == 7
            assert all(field in data['totals'] for field in PERSON_FIELDS)
        assert all(field in row for row in summary['properties'] for field in PERSON_FIELDS)

    def test_window_setting_is_exposed(self, get, status_world, settings):
        settings.NO_SHOW_REPORT_WINDOW_DAYS = 3
        assert get(f'{S}/hotels/').data['no_show_report_window_days'] == 3


class TestBusinessDate:
    """Tashkent is UTC+5: just after its midnight it is already the next day."""

    @pytest.mark.parametrize('utc, expected', [
        (datetime(2026, 10, 6, 18, 59, tzinfo=timezone.utc), '2026-10-06'),
        (datetime(2026, 10, 6, 19, 0, tzinfo=timezone.utc), '2026-10-07'),
        (datetime(2026, 10, 6, 19, 5, tzinfo=timezone.utc), '2026-10-07'),
    ])
    def test_meta_follows_the_business_date(self, utc, expected):
        with mock.patch('common.dates.timezone.now', return_value=utc):
            assert status_meta()['business_date'] == expected

    @pytest.mark.django_db
    def test_endpoint_just_after_tashkent_midnight(self, get, status_world):
        late_utc = datetime(2026, 10, 6, 19, 5, tzinfo=timezone.utc)
        with mock.patch('common.dates.timezone.now', return_value=late_utc):
            assert get(f'{S}/hotels/').data['business_date'] == '2026-10-07'


@pytest.mark.django_db
class TestQueryCountsStayConstant:

    def count(self, get, url):
        with CaptureQueriesContext(connection) as queries:
            assert get(url).status_code == 200
        return len(queries)

    def grow(self, status_world, n):
        guest, beta = status_world['guests'][0], status_world['hotels']['beta']
        for i in range(n):
            persons(make_booking(guest, beta, business_today() - timedelta(days=i + 1), '10.00',
                                 status='completed'), 3)

    @pytest.mark.parametrize('path', ['/countries/', '/hotels/', '/users/'])
    def test_lists(self, get, status_world, path):
        self.grow(status_world, 2)
        small = self.count(get, f'{S}{path}')
        self.grow(status_world, 40)
        assert self.count(get, f'{S}{path}') == small

    def test_hotel_detail(self, get, status_world):
        beta = status_world['hotels']['beta']
        self.grow(status_world, 2)
        small = self.count(get, f'{S}/hotels/{beta.id}/')
        self.grow(status_world, 40)
        assert self.count(get, f'{S}/hotels/{beta.id}/') == small
