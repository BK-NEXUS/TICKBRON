"""
Partner property writes use the Geography dictionary (Geography plan G4):
country_ref, region_ref and city_ref ids are required on create and validated
(active, region inside country, city inside region). The old text fields are
filled from the English names by Property.save().
"""
import pytest
from rest_framework.test import APIClient

from geography.models import City, Country, Region
from permissions.models import Role
from properties.models import Property, PropertyType
from users.models import User

URL = '/api/v1/partner/properties/'


def details(response):
    """Field errors from the uniform error envelope."""
    return response.data['error']['details']


@pytest.fixture
def owner(db):
    role, _ = Role.objects.get_or_create(
        name='hotel-owner', defaults={'description': 'Hotel owner role', 'is_system_role': True})
    return User.objects.create_user(email='owner@example.com', password='OwnerPassword#123', role=role)


@pytest.fixture
def client(owner):
    api = APIClient()
    api.force_authenticate(user=owner)
    return api


@pytest.fixture
def hotel_type(db):
    return PropertyType.objects.create(name='Hotel', slug='hotel')


@pytest.fixture
def world(db):
    xland = Country.objects.create(code='XA', name_uz='Xland', name_ru='Иксландия', name_en='Xland', currency='USD')
    east = Region.objects.create(country=xland, name_uz='Sharq', name_ru='Восток', name_en='East')
    west = Region.objects.create(country=xland, name_uz="G'arb", name_ru='Запад', name_en='West')
    capital = City.objects.create(region=east, name_uz='Poytaxt', name_ru='Столица', name_en='Capital')
    harbour = City.objects.create(region=west, name_uz='Port', name_ru='Порт', name_en='Harbour')
    yland = Country.objects.create(code='XB', name_uz='Yland', name_ru='Игрекландия', name_en='Yland', currency='USD')
    south = Region.objects.create(country=yland, name_uz='Janub', name_ru='Юг', name_en='South')
    return {'xland': xland, 'east': east, 'west': west, 'capital': capital, 'harbour': harbour,
            'yland': yland, 'south': south}


def payload(hotel_type, world, **overrides):
    data = {
        'property_type': hotel_type.id, 'max_guests': 2, 'bedrooms': 1, 'bathrooms': 1,
        'address_line1': '1 Main St', 'base_price': '70.00', 'currency': 'USD',
        'country_ref': world['xland'].id, 'region_ref': world['east'].id, 'city_ref': world['capital'].id,
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
class TestCreate:

    def test_creates_with_refs_and_fills_the_text_fields(self, client, hotel_type, world):
        response = client.post(URL, payload(hotel_type, world), format='json')
        assert response.status_code == 201, response.data
        prop = Property.objects.get(address_line1='1 Main St')
        assert (prop.country_ref_id, prop.region_ref_id, prop.city_ref_id) == (
            world['xland'].id, world['east'].id, world['capital'].id)
        assert (prop.country, prop.state, prop.city) == ('Xland', 'East', 'Capital')

    def test_text_fields_sent_by_the_client_do_not_win_over_the_refs(self, client, hotel_type, world):
        response = client.post(
            URL, payload(hotel_type, world, city='Elsewhere', state='Nowhere', country='Atlantis'), format='json')
        assert response.status_code == 201, response.data
        prop = Property.objects.get(address_line1='1 Main St')
        assert (prop.country, prop.state, prop.city) == ('Xland', 'East', 'Capital')

    @pytest.mark.parametrize('missing', ['country_ref', 'region_ref', 'city_ref'])
    def test_all_three_are_required(self, client, hotel_type, world, missing):
        data = payload(hotel_type, world)
        del data[missing]
        response = client.post(URL, data, format='json')
        assert response.status_code == 400
        assert missing in details(response)
        assert not Property.objects.exists()

    def test_text_only_location_is_rejected(self, client, hotel_type, world):
        data = payload(hotel_type, world, city='Tashkent', country='Uzbekistan')
        for key in ('country_ref', 'region_ref', 'city_ref'):
            del data[key]
        assert client.post(URL, data, format='json').status_code == 400

    def test_null_is_rejected(self, client, hotel_type, world):
        assert client.post(URL, payload(hotel_type, world, city_ref=None), format='json').status_code == 400

    def test_region_must_belong_to_the_country(self, client, hotel_type, world):
        response = client.post(URL, payload(hotel_type, world, region_ref=world['south'].id), format='json')
        assert response.status_code == 400 and 'region_ref' in details(response)

    def test_city_must_belong_to_the_region(self, client, hotel_type, world):
        response = client.post(URL, payload(hotel_type, world, city_ref=world['harbour'].id), format='json')
        assert response.status_code == 400 and 'city_ref' in details(response)

    def test_unknown_ids_are_400(self, client, hotel_type, world):
        response = client.post(URL, payload(hotel_type, world, country_ref=999999), format='json')
        assert response.status_code == 400 and 'country_ref' in details(response)

    @pytest.mark.parametrize('hide', ['xland', 'east', 'capital'])
    def test_hidden_rows_cannot_be_chosen(self, client, hotel_type, world, hide):
        row = world[hide]
        type(row).objects.filter(pk=row.pk).update(is_active=False)
        response = client.post(URL, payload(hotel_type, world), format='json')
        assert response.status_code == 400
        assert not Property.objects.exists()


@pytest.mark.django_db
class TestUpdate:

    @pytest.fixture
    def prop(self, owner, hotel_type, world):
        return Property.objects.create(
            owner=owner, property_type=hotel_type, max_guests=2, address_line1='1 Main St',
            base_price=70, country_ref=world['xland'], region_ref=world['east'], city_ref=world['capital'])

    def test_move_to_another_city_in_the_same_country(self, client, prop, world):
        response = client.patch(f'{URL}{prop.id}/', {
            'region_ref': world['west'].id, 'city_ref': world['harbour'].id}, format='json')
        assert response.status_code == 200, response.data
        prop.refresh_from_db()
        assert (prop.region_ref_id, prop.city_ref_id) == (world['west'].id, world['harbour'].id)
        assert (prop.state, prop.city) == ('West', 'Harbour')

    def test_changing_only_the_region_keeps_the_old_city_and_is_rejected(self, client, prop, world):
        response = client.patch(f'{URL}{prop.id}/', {'region_ref': world['west'].id}, format='json')
        assert response.status_code == 400 and 'city_ref' in details(response)

    def test_changing_only_the_country_is_rejected(self, client, prop, world):
        response = client.patch(f'{URL}{prop.id}/', {'country_ref': world['yland'].id}, format='json')
        assert response.status_code == 400

    def test_other_edits_do_not_revalidate_a_hidden_location(self, client, prop, world):
        City.objects.filter(pk=world['capital'].pk).update(is_active=False)
        response = client.patch(f'{URL}{prop.id}/', {'max_guests': 5}, format='json')
        assert response.status_code == 200, response.data

    def test_refs_are_in_the_response(self, client, prop, world):
        data = client.get(f'{URL}{prop.id}/').data
        assert (data['country_ref'], data['region_ref'], data['city_ref']) == (
            world['xland'].id, world['east'].id, world['capital'].id)

    def test_cannot_clear_a_ref(self, client, prop):
        assert client.patch(f'{URL}{prop.id}/', {'city_ref': None}, format='json').status_code == 400

    def test_legacy_property_without_refs_can_be_edited_and_later_mapped(self, client, owner, hotel_type, world):
        legacy = Property.objects.create(
            owner=owner, property_type=hotel_type, max_guests=2, address_line1='9 Old St', base_price=50,
            city='Somewhere', country='Elsewhere')
        assert client.patch(f'{URL}{legacy.id}/', {'max_guests': 3}, format='json').status_code == 200
        response = client.patch(f'{URL}{legacy.id}/', {
            'country_ref': world['xland'].id, 'region_ref': world['east'].id, 'city_ref': world['capital'].id,
        }, format='json')
        assert response.status_code == 200, response.data
        legacy.refresh_from_db()
        assert legacy.city == 'Capital'
