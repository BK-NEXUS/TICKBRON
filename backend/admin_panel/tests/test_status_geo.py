"""
Admin Status: countries > regions > hotels (Status plan S2).

A booking counts when it is confirmed or completed and not soft-deleted; it belongs
to the period of its check-in date; revenue is grouped per currency.
Hotels are grouped by their Geography refs (Geography plan G4): countries by ISO code, regions by id,
hotels without a ref under "unspecified" (URL segment) / "Unspecified" (label).
Access is covered by test_access_matrix.py. Data: the status_world fixture (status_fixtures.py).
"""
import pytest
from rest_framework.test import APIClient

from geography.models import Region
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


def tashkent_id():
    return Region.objects.get(country__code='UZ', name_en='Tashkent').id


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
        assert (uz['rank'], uz['code'], uz['country'], uz['hotels'], uz['bookings'], uz['guests']) == \
            (1, 'UZ', 'Uzbekistan', 3, 5, 3)
        assert (uz['name_uz'], uz['name_ru'], uz['name_en']) == ("O'zbekiston", 'Узбекистан', 'Uzbekistan')
        # Revenue is grouped per currency, never mixed
        assert revenue(uz) == {'EUR': '60.00', 'USD': '530.00'}
        assert (kz['rank'], kz['code'], kz['country'], kz['hotels'], kz['bookings'], kz['guests']) == \
            (2, 'KZ', 'Kazakhstan', 1, 1, 1)
        assert revenue(kz) == {'KZT': '50000.00'}

    def test_month_period_uses_the_check_in_date(self, get):
        uz, kz = get(f'{S}/countries/', period='2026-04').data['results']

        assert (uz['bookings'], uz['guests']) == (3, 3)
        assert revenue(uz) == {'EUR': '60.00', 'USD': '350.00'}
        assert kz['bookings'] == 1

    def test_year_period(self, get):
        response = get(f'{S}/countries/', period='2025')

        assert response.data['period'] == '2025'
        rows = {row['code']: row for row in response.data['results']}
        assert (rows['UZ']['bookings'], revenue(rows['UZ'])) == (1, {'USD': '80.00'})
        # Countries without bookings in the period stay listed with zeros
        assert (rows['KZ']['bookings'], rows['KZ']['revenue']) == (0, [])

    @pytest.mark.parametrize('period', ['2026-13', '26', 'last-month', '2026-4', '1999'])
    def test_invalid_period_is_400(self, get, period):
        response = get(f'{S}/countries/', period=period)
        assert response.status_code == 400
        assert 'period' in response.data

    @pytest.mark.parametrize('term', ['kaz', 'Qozog', 'Казах'])
    def test_search_filters_the_list_in_every_language(self, get, term):
        response = get(f'{S}/countries/', search=term)
        assert [row['code'] for row in response.data['results']] == ['KZ']

    def test_paginated(self, get):
        response = get(f'{S}/countries/', page_size=1, page=2)

        assert response.data['count'] == 2
        assert [(row['rank'], row['code']) for row in response.data['results']] == [(2, 'KZ')]
        assert response.data['previous'] is not None

    def test_soft_deleted_hotels_are_left_out(self, get, status_world):
        delta = status_world['hotels']['delta']
        delta.is_deleted = True
        delta.save()

        assert [row['code'] for row in get(f'{S}/countries/').data['results']] == ['UZ']

    def test_hotels_without_a_country_are_grouped_as_unspecified(self, get, status_world):
        gamma = status_world['hotels']['gamma']
        type(gamma).objects.filter(pk=gamma.pk).update(country_ref=None, region_ref=None, city_ref=None)

        rows = {row['code']: row for row in get(f'{S}/countries/').data['results']}
        assert rows['UZ']['hotels'] == 2
        assert (rows[None]['country'], rows[None]['hotels'], rows[None]['bookings']) == ('Unspecified', 1, 0)

    def test_text_fields_do_not_decide_the_group(self, get, status_world):
        # The old text location is only a copy: grouping follows the refs
        alpha = status_world['hotels']['alpha']
        type(alpha).objects.filter(pk=alpha.pk).update(country='Atlantis')
        assert 'Atlantis' not in [row['country'] for row in get(f'{S}/countries/').data['results']]


@pytest.mark.django_db
@pytest.mark.usefixtures('status_world')
class TestRegions:

    def test_regions_of_one_country_with_unspecified_group(self, get):
        response = get(f'{S}/countries/UZ/regions/')

        assert response.status_code == 200
        tashkent, unspecified = response.data['results']
        assert (tashkent['id'], tashkent['region'], tashkent['hotels'], tashkent['bookings'], tashkent['guests']) == \
            (tashkent_id(), 'Tashkent', 2, 5, 3)
        assert (tashkent['name_uz'], tashkent['name_ru'], tashkent['name_en']) == \
            ('Toshkent shahri', 'город Ташкент', 'Tashkent')
        assert revenue(tashkent) == {'EUR': '60.00', 'USD': '530.00'}
        assert (unspecified['id'], unspecified['region'], unspecified['hotels'], unspecified['bookings'],
                unspecified['revenue']) == (None, 'Unspecified', 1, 0, [])
        assert (response.data['country'], response.data['country_name']) == ('UZ', 'Uzbekistan')

    def test_country_code_is_case_insensitive(self, get):
        assert get(f'{S}/countries/uz/regions/').data['count'] == 2

    @pytest.mark.parametrize('term', ['tash', 'Toshkent', 'Ташкент'])
    def test_search_in_every_language_and_period(self, get, term):
        response = get(f'{S}/countries/UZ/regions/', search=term, period='2025-11')

        assert [(row['region'], row['bookings']) for row in response.data['results']] == [('Tashkent', 1)]

    def test_unknown_country_is_an_empty_list(self, get):
        response = get(f'{S}/countries/ZZ/regions/')
        assert (response.status_code, response.data['count']) == (200, 0)

    def test_hotels_without_a_country_have_their_own_group(self, get, status_world):
        gamma = status_world['hotels']['gamma']
        type(gamma).objects.filter(pk=gamma.pk).update(country_ref=None)
        response = get(f'{S}/countries/unspecified/regions/')
        assert [(row['id'], row['region'], row['hotels']) for row in response.data['results']] == \
            [(None, 'Unspecified', 1)]
        assert (response.data['country'], response.data['country_name']) == ('unspecified', 'Unspecified')


@pytest.mark.django_db
@pytest.mark.usefixtures('status_world')
class TestHotels:

    def test_hotels_of_one_region(self, get, status_world):
        response = get(f'{S}/countries/UZ/regions/{tashkent_id()}/hotels/')

        assert response.status_code == 200
        alpha, beta = response.data['results']
        assert (alpha['id'], alpha['name'], alpha['city'], alpha['bookings'], alpha['guests']) == \
            (status_world['hotels']['alpha'].id, 'Alpha Hotel', 'Tashkent', 3, 2)
        assert revenue(alpha) == {'USD': '450.00'}
        assert (beta['name'], beta['bookings'], revenue(beta)) == ('Beta Hotel', 2, {'EUR': '60.00', 'USD': '80.00'})
        assert (response.data['country'], response.data['country_name']) == ('UZ', 'Uzbekistan')
        assert (response.data['region'], response.data['region_name']) == (str(tashkent_id()), 'Tashkent')

    def test_unspecified_region_lists_hotels_without_one(self, get):
        response = get(f'{S}/countries/UZ/regions/unspecified/hotels/')
        assert [(row['name'], row['bookings']) for row in response.data['results']] == [('Gamma Hotel', 0)]
        assert (response.data['region'], response.data['region_name']) == ('unspecified', 'Unspecified')

    def test_a_region_of_another_country_has_no_hotels_here(self, get):
        assert get(f'{S}/countries/KZ/regions/{tashkent_id()}/hotels/').data['count'] == 0

    def test_garbage_region_segment_is_an_empty_list(self, get):
        assert get(f'{S}/countries/UZ/regions/Atlantis/hotels/').data['count'] == 0

    def test_search_by_hotel_name(self, get):
        response = get(f'{S}/countries/UZ/regions/{tashkent_id()}/hotels/', search='bet')
        assert [row['name'] for row in response.data['results']] == ['Beta Hotel']

    def test_period(self, get):
        response = get(f'{S}/countries/UZ/regions/{tashkent_id()}/hotels/', period='2026-03')
        assert [(row['name'], row['bookings']) for row in response.data['results']] == \
            [('Alpha Hotel', 1), ('Beta Hotel', 0)]


@pytest.mark.django_db
@pytest.mark.usefixtures('status_world')
class TestAggregatesInTheDatabase:
    """A fixed number of queries per page (count, page, revenue), however many rows there are."""

    @pytest.mark.parametrize('url,queries', [
        (f'{S}/countries/', 3),
        # plus one lookup per parent for the breadcrumb names (country; country and region)
        (f'{S}/countries/UZ/regions/', 4),
        (f'{S}/countries/UZ/regions/{{region}}/hotels/', 5),
    ])
    def test_query_count_is_constant(self, get, django_assert_max_num_queries, url, queries):
        url = url.format(region=tashkent_id())  # looked up outside the counted block
        with django_assert_max_num_queries(queries):
            response = get(url)
        assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.usefixtures('status_world')
class TestDeprecatedNameKeys:
    """
    DEPRECATED (2026-10-02, until the frontend moves to codes and ids, G5-G6): the URL keys may still
    be the names shown in the lists ("Uzbekistan", "Tashkent"); they return the same rows.
    """

    @staticmethod
    def rows(response):
        assert response.status_code == 200
        return response.data['results']

    @pytest.mark.parametrize('key', ['Uzbekistan', 'uzbekistan', 'Узбекистан', 'UZ', 'uz'])
    def test_regions_by_country_name_or_code_are_the_same_rows(self, get, key):
        assert self.rows(get(f'{S}/countries/{key}/regions/')) == self.rows(get(f'{S}/countries/UZ/regions/'))

    def test_the_country_is_echoed_as_sent_for_the_old_client(self, get):
        assert get(f'{S}/countries/Uzbekistan/regions/').data['country'] == 'Uzbekistan'
        assert get(f'{S}/countries/Uzbekistan/regions/').data['country_name'] == 'Uzbekistan'
        assert get(f'{S}/countries/UZ/regions/').data['country'] == 'UZ'

    @pytest.mark.parametrize('region', ['Tashkent', 'tashkent', 'Toshkent shahri', 'город Ташкент'])
    def test_hotels_by_names_are_the_same_rows(self, get, region):
        by_id = self.rows(get(f'{S}/countries/UZ/regions/{tashkent_id()}/hotels/'))
        assert by_id
        assert self.rows(get(f'{S}/countries/Uzbekistan/regions/{region}/hotels/')) == by_id

    def test_hotel_names_response_echoes_the_names_and_resolves_the_labels(self, get):
        response = get(f'{S}/countries/Uzbekistan/regions/Tashkent/hotels/')
        assert (response.data['country'], response.data['region']) == ('Uzbekistan', 'Tashkent')
        assert (response.data['country_name'], response.data['region_name']) == ('Uzbekistan', 'Tashkent')

    def test_unspecified_by_its_label(self, get):
        response = get(f'{S}/countries/Uzbekistan/regions/Unspecified/hotels/')
        assert [row['name'] for row in self.rows(response)] == ['Gamma Hotel']

    def test_a_region_name_of_another_country_is_empty(self, get):
        assert get(f'{S}/countries/Kazakhstan/regions/Tashkent/hotels/').data['count'] == 0

    def test_unknown_names_are_empty_lists(self, get):
        assert get(f'{S}/countries/Atlantis/regions/').data['count'] == 0
        assert get(f'{S}/countries/Uzbekistan/regions/Atlantis/hotels/').data['count'] == 0

    def test_the_whole_old_drill_down_walks_through_the_row_names(self, get):
        # What the current frontend does: it builds the next URL from the names in the previous list
        country = self.rows(get(f'{S}/countries/'))[0]['country']
        region = self.rows(get(f'{S}/countries/{country}/regions/'))[0]['region']
        hotels = self.rows(get(f'{S}/countries/{country}/regions/{region}/hotels/'))
        assert [row['name'] for row in hotels] == ['Alpha Hotel', 'Beta Hotel']
