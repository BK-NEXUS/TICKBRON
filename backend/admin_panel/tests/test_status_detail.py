"""
Admin Status: hotel detail and the guests ranking (Status plan S3).

Access is covered by test_access_matrix.py. Data: the status_world fixture (status_fixtures.py).
"""
import pytest
from rest_framework.test import APIClient

from users.models import User

S = '/api/v1/admin-panel/status'


@pytest.fixture
def get(db):
    staff = User.objects.create_user(email='staff@example.com', password='StaffPassword#123', is_staff=True)
    client = APIClient()
    client.force_authenticate(user=staff)

    def _get(url, **params):
        return client.get(url, params)
    return _get


def revenue(row):
    return {item['currency']: item['amount'] for item in row['revenue']}


@pytest.mark.django_db
class TestHotelDetail:

    def test_info_totals_and_monthly_series(self, get, status_world):
        alpha = status_world['hotels']['alpha']
        owner = status_world['owners'][0]

        response = get(f'{S}/hotels/{alpha.id}/', year=2026)

        assert response.status_code == 200
        hotel = response.data['hotel']
        assert (hotel['id'], hotel['name'], hotel['city'], hotel['region'], hotel['country']) == \
            (alpha.id, 'Alpha Hotel', 'Tashkent', 'Tashkent', 'Uzbekistan')
        assert hotel['address'] == alpha.get_full_address()
        assert hotel['registered_at'] is not None
        assert hotel['owner'] == {
            'id': owner.id, 'name': 'Olim Owner', 'email': 'owner1@example.com', 'phone': '+998901111111',
        }

        totals = response.data['totals']
        assert (totals['bookings'], totals['guests'], revenue(totals)) == (3, 2, {'USD': '450.00'})

        assert response.data['year'] == 2026
        assert response.data['available_years'] == [2026]
        months = {row['month']: row for row in response.data['monthly']}
        assert list(months) == [f'2026-{m:02d}' for m in range(1, 13)]
        assert (months['2026-03']['bookings'], months['2026-03']['guests'], revenue(months['2026-03'])) == \
            (1, 1, {'USD': '100.00'})
        assert (months['2026-04']['bookings'], months['2026-04']['guests'], revenue(months['2026-04'])) == \
            (2, 2, {'USD': '350.00'})
        assert (months['2026-05']['bookings'], months['2026-05']['revenue']) == (0, [])

    def test_totals_follow_the_period(self, get, status_world):
        alpha = status_world['hotels']['alpha']
        totals = get(f'{S}/hotels/{alpha.id}/', period='2026-03').data['totals']
        assert (totals['bookings'], revenue(totals)) == (1, {'USD': '100.00'})

    def test_hotel_without_region_is_unspecified(self, get, status_world):
        gamma = status_world['hotels']['gamma']
        response = get(f'{S}/hotels/{gamma.id}/')
        assert response.data['hotel']['region'] == 'Unspecified'
        assert response.data['totals']['bookings'] == 0

    @pytest.mark.parametrize('params', [{'year': '26'}, {'year': 'abc'}, {'period': '2026-00'}])
    def test_invalid_year_or_period_is_400(self, get, status_world, params):
        alpha = status_world['hotels']['alpha']
        assert get(f'{S}/hotels/{alpha.id}/', **params).status_code == 400

    def test_unknown_or_deleted_hotel_is_404(self, get, status_world):
        gamma = status_world['hotels']['gamma']
        gamma.is_deleted = True
        gamma.save()
        assert get(f'{S}/hotels/{gamma.id}/').status_code == 404
        assert get(f'{S}/hotels/999999/').status_code == 404


@pytest.mark.django_db
class TestUsers:

    def test_guests_ranked_by_counted_bookings(self, get, status_world):
        g1, g2, g3 = status_world['guests']

        response = get(f'{S}/users/')

        assert response.status_code == 200
        rows = response.data['results']
        # Everyone has 2 counted bookings: ties go to the most recent stay first
        assert [row['id'] for row in rows] == [g2.id, g1.id, g3.id]
        first = rows[0]
        assert (first['rank'], first['full_name'], first['first_name'], first['last_name']) == \
            (1, 'Madina Nazarova', 'Madina', 'Nazarova')
        assert (first['phone'], first['email'], first['bookings'], first['last_booking_date']) == \
            ('+998903330002', 'guest2@example.com', 2, '2026-04-12')
        assert revenue({'revenue': first['total_spent']}) == {'USD': '280.00'}
        assert revenue({'revenue': rows[2]['total_spent']}) == {'EUR': '60.00', 'KZT': '50000.00'}
        # Hotel owners and staff without counted bookings are not listed
        assert response.data['count'] == 3

    def test_period(self, get, status_world):
        g2 = status_world['guests'][1]
        rows = get(f'{S}/users/', period='2025').data['results']
        assert [(row['id'], row['bookings']) for row in rows] == [(g2.id, 1)]

    @pytest.mark.parametrize('search,expected', [
        ('naz', ['guest2@example.com']),          # last name, partial
        ('TIM', ['guest3@example.com']),          # first name, any case
        ('guest1@', ['guest1@example.com']),      # email
        ('3330003', ['guest3@example.com']),      # phone, partial
    ])
    def test_search(self, get, status_world, search, expected):
        rows = get(f'{S}/users/', search=search).data['results']
        assert [row['email'] for row in rows] == expected

    def test_search_by_id(self, get, status_world):
        g3 = status_world['guests'][2]
        rows = get(f'{S}/users/', search=str(g3.id)).data['results']
        assert g3.id in [row['id'] for row in rows]

    def test_invalid_period_is_400(self, get, status_world):
        assert get(f'{S}/users/', period='soon').status_code == 400


@pytest.mark.django_db
class TestAggregatesInTheDatabase:
    """A fixed number of queries, however many bookings or guests there are."""

    def test_hotel_detail(self, get, status_world, django_assert_max_num_queries):
        alpha = status_world['hotels']['alpha']
        # hotel, totals, totals revenue, years, monthly counts, monthly revenue
        with django_assert_max_num_queries(6):
            assert get(f'{S}/hotels/{alpha.id}/', year=2026).status_code == 200

    def test_users(self, get, status_world, django_assert_max_num_queries):
        # count, page, total spent for the page's guests
        with django_assert_max_num_queries(3):
            assert get(f'{S}/users/').status_code == 200
