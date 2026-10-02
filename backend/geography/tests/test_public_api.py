"""
Public geography API (Geography plan G3):

    GET /api/v1/geography/countries/
    GET /api/v1/geography/countries/{code}/regions/
    GET /api/v1/geography/regions/{id}/cities/

Active rows only, all three names in every row, hotel counts from one annotated query.
"""
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from geography.models import City, Country, Region
from properties.models import Property, PropertyType
from users.models import User

BASE = '/api/v1/geography'


@pytest.fixture
def world(db):
    country = Country.objects.create(code='XA', name_uz='Xland', name_ru='Иксландия', name_en='Xland',
                                     currency='USD')
    east = Region.objects.create(country=country, name_uz='Sharq', name_ru='Восток', name_en='East', sort_order=1)
    west = Region.objects.create(country=country, name_uz='G\'arb', name_ru='Запад', name_en='West', sort_order=2)
    capital = City.objects.create(region=east, name_uz='Poytaxt', name_ru='Столица', name_en='Capital', sort_order=1)
    port = City.objects.create(region=east, name_uz='Port', name_ru='Порт', name_en='Port', sort_order=2)
    return {'country': country, 'east': east, 'west': west, 'capital': capital, 'port': port}


def make_property(owner, n, country=None, region=None, city=None, **extra):
    hotel_type, _ = PropertyType.objects.get_or_create(slug='hotel', defaults={'name': 'Hotel'})
    fields = dict(status='active', is_active=True)
    fields.update(extra)
    return Property.objects.create(
        owner=owner, property_type=hotel_type, max_guests=2, address_line1=f'{n} Main St',
        base_price=Decimal('50.00'), country_ref=country, region_ref=region, city_ref=city, **fields)


@pytest.fixture
def owner(db):
    return User.objects.create_user(email='owner@example.com', password='OwnerPassword#123')


def get(url, **params):
    return APIClient().get(f'{BASE}{url}', params)


@pytest.mark.django_db
class TestCountries:

    def test_is_public_and_lists_active_countries_with_all_names(self, world):
        Country.objects.create(code='XB', name_uz='B', name_ru='Б', name_en='Bland', currency='USD',
                               is_active=False)
        response = get('/countries/')
        assert response.status_code == 200
        row = next(r for r in response.data if r['code'] == 'XA')
        assert (row['name_uz'], row['name_ru'], row['name_en']) == ('Xland', 'Иксландия', 'Xland')
        assert row['currency'] == 'USD'
        assert 'XB' not in [r['code'] for r in response.data]

    def test_ordered_by_sort_order_then_name(self, world):
        for code, name, order in (('QA', 'Zed', 900), ('QB', 'Abe', 900), ('QC', 'Zzz', 899)):
            Country.objects.create(code=code, name_uz=name, name_ru=name, name_en=name, currency='USD',
                                   sort_order=order)
        codes = [r['code'] for r in get('/countries/').data if r['code'].startswith('Q')]
        assert codes == ['QC', 'QB', 'QA']

    def test_hotel_count_counts_only_public_properties_and_ignores_hidden_ones(self, world, owner):
        c = world
        make_property(owner, 1, c['country'], c['east'], c['capital'])
        make_property(owner, 2, c['country'], c['east'], c['port'])
        make_property(owner, 3, c['country'], c['east'], c['port'], status='pending_approval')
        make_property(owner, 4, c['country'], c['east'], c['port'], is_active=False)
        make_property(owner, 5, c['country'], c['east'], c['port'], is_deleted=True)
        row = next(r for r in get('/countries/').data if r['code'] == 'XA')
        assert row['hotel_count'] == 2

    def test_one_query_for_any_number_of_countries(self, world, owner):
        for i in range(5):
            country = Country.objects.create(code=f'Y{i}', name_uz='n', name_ru='н', name_en=f'N{i}', currency='USD')
            make_property(owner, i, country)
        with CaptureQueriesContext(connection) as queries:
            assert get('/countries/').status_code == 200
        assert len(queries) == 1


@pytest.mark.django_db
class TestRegions:

    def test_lists_active_regions_of_the_country_with_counts(self, world, owner):
        c = world
        Region.objects.create(country=c['country'], name_uz='H', name_ru='С', name_en='Hidden', is_active=False)
        make_property(owner, 1, c['country'], c['east'], c['capital'])
        response = get('/countries/XA/regions/')
        assert response.status_code == 200
        assert [r['name_en'] for r in response.data] == ['East', 'West']
        assert [r['hotel_count'] for r in response.data] == [1, 0]
        assert set(response.data[0]) >= {'id', 'name_uz', 'name_ru', 'name_en', 'hotel_count'}

    def test_code_is_case_insensitive(self, world):
        assert get('/countries/xa/regions/').status_code == 200

    def test_unknown_or_hidden_country_is_404(self, world):
        assert get('/countries/ZZ/regions/').status_code == 404
        Country.objects.filter(code='XA').update(is_active=False)
        assert get('/countries/XA/regions/').status_code == 404


@pytest.mark.django_db
class TestCities:

    def test_lists_active_cities_of_the_region_with_counts(self, world, owner):
        c = world
        City.objects.create(region=c['east'], name_uz='H', name_ru='С', name_en='Hidden', is_active=False)
        make_property(owner, 1, c['country'], c['east'], c['port'])
        response = get(f"/regions/{c['east'].id}/cities/")
        assert response.status_code == 200
        assert [r['name_en'] for r in response.data] == ['Capital', 'Port']
        assert [r['hotel_count'] for r in response.data] == [0, 1]

    def test_unknown_hidden_region_or_hidden_country_is_404(self, world):
        c = world
        assert get('/regions/999999/cities/').status_code == 404
        Region.objects.filter(pk=c['east'].pk).update(is_active=False)
        assert get(f"/regions/{c['east'].id}/cities/").status_code == 404
        Region.objects.filter(pk=c['east'].pk).update(is_active=True)
        Country.objects.filter(pk=c['country'].pk).update(is_active=False)
        assert get(f"/regions/{c['east'].id}/cities/").status_code == 404

    def test_read_only(self, world):
        client = APIClient()
        for url in ('/countries/', '/countries/XA/regions/', f"/regions/{world['east'].id}/cities/"):
            assert client.post(f'{BASE}{url}', {}, format='json').status_code == 405
