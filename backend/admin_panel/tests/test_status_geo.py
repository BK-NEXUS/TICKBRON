"""
Admin Status: countries > regions > hotels (Status plan S2).

A booking counts when it is confirmed or completed and not soft-deleted; it belongs
to the period of its check-in date; revenue is grouped per currency.
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
@pytest.mark.usefixtures('status_world')
class TestCountries:

    def test_ranks_countries_with_counted_bookings_only(self, get):
        response = get(f'{S}/countries/')

        assert response.status_code == 200
        assert response.data['period'] == 'all'
        assert response.data['count'] == 2
        uz, kz = response.data['results']
        assert (uz['rank'], uz['country'], uz['hotels'], uz['bookings'], uz['guests']) == \
            (1, 'Uzbekistan', 3, 5, 3)
        # Revenue is grouped per currency, never mixed
        assert revenue(uz) == {'EUR': '60.00', 'USD': '530.00'}
        assert (kz['rank'], kz['country'], kz['hotels'], kz['bookings'], kz['guests']) == \
            (2, 'Kazakhstan', 1, 1, 1)
        assert revenue(kz) == {'KZT': '50000.00'}

    def test_month_period_uses_the_check_in_date(self, get):
        uz, kz = get(f'{S}/countries/', period='2026-04').data['results']

        assert (uz['bookings'], uz['guests']) == (3, 3)
        assert revenue(uz) == {'EUR': '60.00', 'USD': '350.00'}
        assert kz['bookings'] == 1

    def test_year_period(self, get):
        response = get(f'{S}/countries/', period='2025')

        assert response.data['period'] == '2025'
        rows = {row['country']: row for row in response.data['results']}
        assert (rows['Uzbekistan']['bookings'], revenue(rows['Uzbekistan'])) == (1, {'USD': '80.00'})
        # Countries without bookings in the period stay listed with zeros
        assert (rows['Kazakhstan']['bookings'], rows['Kazakhstan']['revenue']) == (0, [])

    @pytest.mark.parametrize('period', ['2026-13', '26', 'last-month', '2026-4', '1999'])
    def test_invalid_period_is_400(self, get, period):
        response = get(f'{S}/countries/', period=period)
        assert response.status_code == 400
        assert 'period' in response.data

    def test_search_filters_the_list(self, get):
        response = get(f'{S}/countries/', search='kaz')
        assert [row['country'] for row in response.data['results']] == ['Kazakhstan']

    def test_paginated(self, get):
        response = get(f'{S}/countries/', page_size=1, page=2)

        assert response.data['count'] == 2
        assert [(row['rank'], row['country']) for row in response.data['results']] == [(2, 'Kazakhstan')]
        assert response.data['previous'] is not None

    def test_soft_deleted_hotels_are_left_out(self, get, status_world):
        delta = status_world['hotels']['delta']
        delta.is_deleted = True
        delta.save()

        assert [row['country'] for row in get(f'{S}/countries/').data['results']] == ['Uzbekistan']


@pytest.mark.django_db
@pytest.mark.usefixtures('status_world')
class TestRegions:

    def test_regions_of_one_country_with_unspecified_group(self, get):
        response = get(f'{S}/countries/Uzbekistan/regions/')

        assert response.status_code == 200
        tashkent, unspecified = response.data['results']
        assert (tashkent['region'], tashkent['hotels'], tashkent['bookings'], tashkent['guests']) == \
            ('Tashkent', 2, 5, 3)
        assert revenue(tashkent) == {'EUR': '60.00', 'USD': '530.00'}
        assert (unspecified['region'], unspecified['hotels'], unspecified['bookings'], unspecified['revenue']) == \
            ('Unspecified', 1, 0, [])
        assert response.data['country'] == 'Uzbekistan'

    def test_search_and_period(self, get):
        response = get(f'{S}/countries/Uzbekistan/regions/', search='tash', period='2025-11')

        assert [(row['region'], row['bookings']) for row in response.data['results']] == [('Tashkent', 1)]

    def test_unknown_country_is_an_empty_list(self, get):
        response = get(f'{S}/countries/Atlantis/regions/')
        assert (response.status_code, response.data['count']) == (200, 0)


@pytest.mark.django_db
@pytest.mark.usefixtures('status_world')
class TestHotels:

    def test_hotels_of_one_region(self, get, status_world):
        response = get(f'{S}/countries/Uzbekistan/regions/Tashkent/hotels/')

        assert response.status_code == 200
        alpha, beta = response.data['results']
        assert (alpha['id'], alpha['name'], alpha['city'], alpha['bookings'], alpha['guests']) == \
            (status_world['hotels']['alpha'].id, 'Alpha Hotel', 'Tashkent', 3, 2)
        assert revenue(alpha) == {'USD': '450.00'}
        assert (beta['name'], beta['bookings'], revenue(beta)) == ('Beta Hotel', 2, {'EUR': '60.00', 'USD': '80.00'})
        assert (response.data['country'], response.data['region']) == ('Uzbekistan', 'Tashkent')

    def test_unspecified_region_lists_hotels_without_one(self, get):
        response = get(f'{S}/countries/Uzbekistan/regions/Unspecified/hotels/')
        assert [(row['name'], row['bookings']) for row in response.data['results']] == [('Gamma Hotel', 0)]

    def test_search_by_hotel_name(self, get):
        response = get(f'{S}/countries/Uzbekistan/regions/Tashkent/hotels/', search='bet')
        assert [row['name'] for row in response.data['results']] == ['Beta Hotel']

    def test_period(self, get):
        response = get(f'{S}/countries/Uzbekistan/regions/Tashkent/hotels/', period='2026-03')
        assert [(row['name'], row['bookings']) for row in response.data['results']] == \
            [('Alpha Hotel', 1), ('Beta Hotel', 0)]


@pytest.mark.django_db
@pytest.mark.usefixtures('status_world')
class TestAggregatesInTheDatabase:
    """A fixed number of queries per page (count, page, revenue), however many rows there are."""

    @pytest.mark.parametrize('url', [
        f'{S}/countries/',
        f'{S}/countries/Uzbekistan/regions/',
        f'{S}/countries/Uzbekistan/regions/Tashkent/hotels/',
    ])
    def test_query_count_is_constant(self, get, django_assert_max_num_queries, url):
        with django_assert_max_num_queries(3):
            response = get(url)
        assert response.status_code == 200
