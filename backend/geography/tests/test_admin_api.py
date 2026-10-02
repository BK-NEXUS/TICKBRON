"""
Super-admin geography CRUD (Geography plan G3) under /api/v1/admin-panel/geography/:

    countries/, regions/, cities/   list (search, filters), create, retrieve, update, delete
    {kind}/reorder/                 POST {"ids": [...]} sets sort_order by position

Hide/show is PATCH {"is_active": false}. Rows in use cannot be deleted (PROTECT), only hidden.
Who may call what is in test_access_matrix.py.
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from geography.models import City, Country, Region
from properties.models import Property, PropertyType
from users.models import User

BASE = '/api/v1/admin-panel/geography'


@pytest.fixture
def admin(db):
    return User.objects.create_superuser(email='admin@example.com', password='AdminPassword#123')


@pytest.fixture
def client(admin):
    api = APIClient()
    api.force_authenticate(user=admin)
    return api


@pytest.fixture
def world(db):
    country = Country.objects.create(code='XA', name_uz='Xland', name_ru='Иксландия', name_en='Xland',
                                     currency='USD')
    region = Region.objects.create(country=country, name_uz='Sharq', name_ru='Восток', name_en='East')
    city = City.objects.create(region=region, name_uz='Poytaxt', name_ru='Столица', name_en='Capital')
    return country, region, city


def use(world):
    """Put a property on the world's city, so nothing in it can be deleted."""
    country, region, city = world
    owner = User.objects.create_user(email='owner@example.com', password='OwnerPassword#123')
    hotel_type, _ = PropertyType.objects.get_or_create(slug='hotel', defaults={'name': 'Hotel'})
    return Property.objects.create(
        owner=owner, property_type=hotel_type, max_guests=2, address_line1='1 Main St',
        base_price=Decimal('50.00'), status='active', country_ref=country, region_ref=region, city_ref=city)


@pytest.mark.django_db
class TestCountries:

    def test_create_normalises_the_codes_and_lists_it(self, client):
        response = client.post(f'{BASE}/countries/', {
            'code': 'xb', 'currency': 'eur', 'name_uz': 'Bland', 'name_ru': 'Бландия', 'name_en': 'Bland',
        }, format='json')
        assert response.status_code == 201, response.data
        assert (response.data['code'], response.data['currency'], response.data['is_active']) == ('XB', 'EUR', True)
        assert 'XB' in [row['code'] for row in client.get(f'{BASE}/countries/').data['results']]

    @pytest.mark.parametrize('field,value', [
        ('code', 'XYZ'), ('code', 'X1'), ('currency', 'US'), ('name_en', ''), ('name_ru', ''), ('name_uz', ''),
    ])
    def test_invalid_values_are_400(self, client, field, value):
        data = {'code': 'XB', 'currency': 'USD', 'name_uz': 'B', 'name_ru': 'Б', 'name_en': 'B'}
        data[field] = value
        assert client.post(f'{BASE}/countries/', data, format='json').status_code == 400

    def test_duplicate_code_is_400_not_500(self, client, world):
        response = client.post(f'{BASE}/countries/', {
            'code': 'XA', 'currency': 'USD', 'name_uz': 'D', 'name_ru': 'Д', 'name_en': 'Dup',
        }, format='json')
        assert response.status_code == 400

    def test_list_includes_hidden_rows_and_counts(self, client, world):
        country = world[0]
        use(world)
        Country.objects.create(code='XB', name_uz='B', name_ru='Б', name_en='Bland', currency='USD', is_active=False)
        rows = {row['code']: row for row in client.get(f'{BASE}/countries/', {'page_size': 100}).data['results']}
        assert rows['XB']['is_active'] is False
        assert (rows['XA']['region_count'], rows['XA']['hotel_count']) == (1, 1)
        assert rows['XA']['id'] == country.id

    def test_hide_and_show(self, client, world):
        country = world[0]
        response = client.patch(f'{BASE}/countries/{country.id}/', {'is_active': False}, format='json')
        assert response.status_code == 200 and response.data['is_active'] is False
        country.refresh_from_db()
        assert country.is_active is False
        client.patch(f'{BASE}/countries/{country.id}/', {'is_active': True}, format='json')
        country.refresh_from_db()
        assert country.is_active is True

    def test_edit_names_keeps_the_stable_fields(self, client, world):
        country, region, _ = world
        response = client.patch(f'{BASE}/countries/{country.id}/', {'name_en': 'Xlandia'}, format='json')
        assert response.status_code == 200 and response.data['name_en'] == 'Xlandia'
        response = client.patch(f'{BASE}/regions/{region.id}/', {'name_en': 'Orient'}, format='json')
        region.refresh_from_db()
        assert (region.name_en, region.slug) == ('Orient', 'xa-east')  # the slug is set once

    def test_search_matches_any_language_and_the_code(self, client, world):
        for term in ('Xland', 'иксл', 'XA', 'xa'):
            rows = client.get(f'{BASE}/countries/', {'search': term}).data['results']
            assert [r['code'] for r in rows] == ['XA'], term
        assert client.get(f'{BASE}/countries/', {'search': 'nothing-like-this'}).data['count'] == 0

    def test_filter_by_active(self, client, world):
        Country.objects.filter(code='XA').update(is_active=False)
        rows = client.get(f'{BASE}/countries/', {'is_active': 'false', 'page_size': 100}).data['results']
        assert [r['code'] for r in rows] == ['XA']

    def test_delete_unused_country_works_but_a_used_one_is_409(self, client, world):
        spare = Country.objects.create(code='XB', name_uz='B', name_ru='Б', name_en='Bland', currency='USD')
        assert client.delete(f'{BASE}/countries/{spare.id}/').status_code == 204
        assert not Country.objects.filter(code='XB').exists()
        response = client.delete(f'{BASE}/countries/{world[0].id}/')  # has a region
        assert response.status_code == 409
        assert Country.objects.filter(code='XA').exists()


@pytest.mark.django_db
class TestRegions:

    def test_create_under_a_country_and_filter_by_country(self, client, world):
        country = world[0]
        response = client.post(f'{BASE}/regions/', {
            'country': country.id, 'name_uz': 'G\'arb', 'name_ru': 'Запад', 'name_en': 'West',
        }, format='json')
        assert response.status_code == 201, response.data
        assert response.data['slug'] == 'xa-west'
        rows = client.get(f'{BASE}/regions/', {'country': country.id}).data['results']
        assert sorted(r['name_en'] for r in rows) == ['East', 'West']
        assert client.get(f'{BASE}/regions/', {'country': 999999}).data['count'] == 0

    def test_unknown_country_and_duplicate_name_are_400(self, client, world):
        country = world[0]
        data = {'country': 999999, 'name_uz': 'G', 'name_ru': 'З', 'name_en': 'West'}
        assert client.post(f'{BASE}/regions/', data, format='json').status_code == 400
        data.update(country=country.id, name_en='East')
        assert client.post(f'{BASE}/regions/', data, format='json').status_code == 400

    def test_the_parent_cannot_be_changed(self, client, world):
        country, region, _ = world
        other = Country.objects.create(code='XB', name_uz='B', name_ru='Б', name_en='Bland', currency='USD')
        response = client.patch(f'{BASE}/regions/{region.id}/', {'country': other.id}, format='json')
        assert response.status_code == 400
        region.refresh_from_db()
        assert region.country_id == country.id

    def test_search_in_all_languages(self, client, world):
        for term in ('East', 'восто', 'sharq'):
            assert client.get(f'{BASE}/regions/', {'search': term}).data['count'] == 1, term

    def test_delete_with_cities_or_properties_is_409_otherwise_204(self, client, world):
        country, region, city = world
        assert client.delete(f'{BASE}/regions/{region.id}/').status_code == 409
        spare = Region.objects.create(country=country, name_uz='S', name_ru='С', name_en='Spare')
        assert client.delete(f'{BASE}/regions/{spare.id}/').status_code == 204


@pytest.mark.django_db
class TestCities:

    def test_create_and_filter_by_region(self, client, world):
        _, region, _ = world
        response = client.post(f'{BASE}/cities/', {
            'region': region.id, 'name_uz': 'Port', 'name_ru': 'Порт', 'name_en': 'Port',
        }, format='json')
        assert response.status_code == 201, response.data
        assert response.data['slug'] == 'xa-east-port'
        rows = client.get(f'{BASE}/cities/', {'region': region.id}).data['results']
        assert sorted(r['name_en'] for r in rows) == ['Capital', 'Port']

    def test_delete_city_in_use_is_409_and_hiding_it_works(self, client, world):
        _, _, city = world
        use(world)
        assert client.delete(f'{BASE}/cities/{city.id}/').status_code == 409
        assert City.objects.filter(pk=city.pk).exists()
        assert client.patch(f'{BASE}/cities/{city.id}/', {'is_active': False}, format='json').status_code == 200

    def test_delete_unused_city_is_204(self, client, world):
        _, region, _ = world
        spare = City.objects.create(region=region, name_uz='S', name_ru='С', name_en='Spare')
        assert client.delete(f'{BASE}/cities/{spare.id}/').status_code == 204


@pytest.mark.django_db
class TestReorder:

    def test_sets_sort_order_by_position(self, client, world):
        country = world[0]
        a = Region.objects.create(country=country, name_uz='A', name_ru='А', name_en='Alpha')
        b = Region.objects.create(country=country, name_uz='B', name_ru='Б', name_en='Beta')
        east = world[1]
        response = client.post(f'{BASE}/regions/reorder/', {'ids': [b.id, east.id, a.id]}, format='json')
        assert response.status_code == 200
        assert [r['name_en'] for r in client.get(f'{BASE}/regions/', {'country': country.id}).data['results']] == [
            'Beta', 'East', 'Alpha']

    @pytest.mark.parametrize('body', [{}, {'ids': 'x'}, {'ids': [1, 'a']}, {'ids': [1, 1]}, {'ids': []}])
    def test_bad_body_is_400(self, client, world, body):
        assert client.post(f'{BASE}/regions/reorder/', body, format='json').status_code == 400

    def test_unknown_ids_are_400_and_nothing_changes(self, client, world):
        east = world[1]
        response = client.post(f'{BASE}/regions/reorder/', {'ids': [east.id, 999999]}, format='json')
        assert response.status_code == 400
        east.refresh_from_db()
        assert east.sort_order == 0

    def test_works_for_countries_and_cities(self, client, world):
        country, region, city = world
        other = City.objects.create(region=region, name_uz='O', name_ru='О', name_en='Other')
        assert client.post(f'{BASE}/cities/reorder/', {'ids': [other.id, city.id]}, format='json').status_code == 200
        other.refresh_from_db()
        assert other.sort_order < City.objects.get(pk=city.pk).sort_order
        assert client.post(f'{BASE}/countries/reorder/', {'ids': [country.id]}, format='json').status_code == 200
