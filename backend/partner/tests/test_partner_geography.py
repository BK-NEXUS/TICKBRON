"""
Partner mehmanxana jazıwları Geografiya sózligin paydalanadı (Geography reje G4; 2026-11-10 den beri regiondan
tómen qala yamasa tuman joq): country_ref hám region_ref id leri jaratıwda májbúriy hám tekseriledi (aktiv, region
mámleket ishinde). country / state / city tekst maydanları tek oqıw nusqaları: Property.save() olardı mámleket hám
regionnıń inglizsha atlarınan toltıradı ("city" nusqası regionnıń atı, sol sebepli orındı kórsetetuǵın hár ekran
islewin dawam etedi). Iye qalanı teriwmeydi.
"""
import pytest
from rest_framework.test import APIClient

from geography.models import Country, Region
from permissions.models import Role
from properties.models import Property, PropertyType
from users.models import User

URL = '/api/v1/partner/properties/'


def details(response):
    """Birdey qátelik konvertinen maydan qátelikleri."""
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
    yland = Country.objects.create(code='XB', name_uz='Yland', name_ru='Игрекландия', name_en='Yland', currency='USD')
    south = Region.objects.create(country=yland, name_uz='Janub', name_ru='Юг', name_en='South')
    return {'xland': xland, 'east': east, 'west': west, 'yland': yland, 'south': south}


def payload(hotel_type, world, **overrides):
    data = {
        'property_type': hotel_type.id, 'max_guests': 2, 'bedrooms': 1, 'bathrooms': 1,
        'address_line1': '1 Main St', 'base_price': '70.00', 'currency': 'USD',
        'translations': {'en': {'name': 'Test Hotel'}},
        'country_ref': world['xland'].id, 'region_ref': world['east'].id,
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
class TestCreate:

    def test_creates_with_refs_and_fills_the_country_region_and_place_text(self, client, hotel_type, world):
        response = client.post(URL, payload(hotel_type, world), format='json')
        assert response.status_code == 201, response.data
        prop = Property.objects.get(address_line1='1 Main St')
        assert (prop.country_ref_id, prop.region_ref_id) == (world['xland'].id, world['east'].id)
        assert (prop.country, prop.state, prop.city) == ('Xland', 'East', 'East')

    def test_the_old_text_sent_by_the_client_does_not_win_over_the_refs(self, client, hotel_type, world):
        response = client.post(
            URL, payload(hotel_type, world, state='Nowhere', country='Atlantis', city='Poseidonia'), format='json')
        assert response.status_code == 201, response.data
        prop = Property.objects.get(address_line1='1 Main St')
        assert (prop.country, prop.state, prop.city) == ('Xland', 'East', 'East')

    def test_a_city_reference_is_ignored_because_there_is_no_city_dictionary(self, client, hotel_type, world):
        response = client.post(URL, payload(hotel_type, world, city_ref=1), format='json')
        assert response.status_code == 201, response.data
        assert 'city_ref' not in response.data

    @pytest.mark.parametrize('missing', ['country_ref', 'region_ref'])
    def test_both_are_required(self, client, hotel_type, world, missing):
        data = payload(hotel_type, world)
        del data[missing]
        response = client.post(URL, data, format='json')
        assert response.status_code == 400
        assert missing in details(response)
        assert not Property.objects.exists()

    def test_null_is_rejected(self, client, hotel_type, world):
        assert client.post(URL, payload(hotel_type, world, region_ref=None), format='json').status_code == 400

    def test_region_must_belong_to_the_country(self, client, hotel_type, world):
        response = client.post(URL, payload(hotel_type, world, region_ref=world['south'].id), format='json')
        assert response.status_code == 400 and 'region_ref' in details(response)

    def test_unknown_ids_are_400(self, client, hotel_type, world):
        response = client.post(URL, payload(hotel_type, world, country_ref=999999), format='json')
        assert response.status_code == 400 and 'country_ref' in details(response)

    @pytest.mark.parametrize('hide', ['xland', 'east'])
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
            base_price=70, country_ref=world['xland'], region_ref=world['east'])

    def test_move_to_another_region_in_the_same_country(self, client, prop, world):
        response = client.patch(f'{URL}{prop.id}/', {'region_ref': world['west'].id}, format='json')
        assert response.status_code == 200, response.data
        prop.refresh_from_db()
        assert prop.region_ref_id == world['west'].id
        assert (prop.state, prop.city) == ('West', 'West')

    def test_a_town_sent_on_an_edit_changes_nothing(self, client, prop):
        response = client.patch(f'{URL}{prop.id}/', {'city': 'Harbour Town', 'max_guests': 3}, format='json')
        assert response.status_code == 200, response.data
        prop.refresh_from_db()
        assert (prop.city, prop.max_guests) == ('East', 3)

    def test_changing_only_the_country_is_rejected(self, client, prop, world):
        response = client.patch(f'{URL}{prop.id}/', {'country_ref': world['yland'].id}, format='json')
        assert response.status_code == 400

    def test_other_edits_do_not_revalidate_a_hidden_location(self, client, prop, world):
        Region.objects.filter(pk=world['east'].pk).update(is_active=False)
        response = client.patch(f'{URL}{prop.id}/', {'max_guests': 5}, format='json')
        assert response.status_code == 200, response.data

    def test_refs_and_the_place_text_are_in_the_response(self, client, prop, world):
        data = client.get(f'{URL}{prop.id}/').data
        assert (data['country_ref'], data['region_ref'], data['city']) == (
            world['xland'].id, world['east'].id, 'East')
        assert 'city_ref' not in data

    def test_cannot_clear_a_ref(self, client, prop):
        assert client.patch(f'{URL}{prop.id}/', {'region_ref': None}, format='json').status_code == 400

    def test_legacy_property_without_refs_can_be_edited_and_later_mapped(self, client, owner, hotel_type, world):
        legacy = Property.objects.create(
            owner=owner, property_type=hotel_type, max_guests=2, address_line1='9 Old St', base_price=50,
            city='Somewhere', country='Elsewhere')
        assert client.patch(f'{URL}{legacy.id}/', {'max_guests': 3}, format='json').status_code == 200
        response = client.patch(f'{URL}{legacy.id}/', {
            'country_ref': world['xland'].id, 'region_ref': world['east'].id,
        }, format='json')
        assert response.status_code == 200, response.data
        legacy.refresh_from_db()
        assert (legacy.country, legacy.state, legacy.city) == ('Xland', 'East', 'East')


@pytest.mark.django_db
class TestOldTextIsNotInput:
    """Eski wizard id ler ornına country / state tekst jiberdi; 2026-10-19 dan beri tek id ler esaplanadı."""

    @pytest.fixture
    def uz(self, db):
        return {
            'country': Country.objects.get(code='UZ'),
            'tashkent': Region.objects.get(country__code='UZ', name_en='Tashkent'),
            'samarkand': Region.objects.get(country__code='UZ', name_en='Samarkand'),
        }

    def payload(self, hotel_type, **extra):
        data = {
            'property_type': hotel_type.id, 'max_guests': 2, 'bedrooms': 1, 'bathrooms': 1,
            'address_line1': '1 Main St', 'base_price': '70.00', 'currency': 'USD', 'translations': {'en': {'name': 'Test Hotel'}},
        }
        data.update(extra)
        return data

    TEXT = {'country': 'Uzbekistan', 'state': 'Tashkent City', 'city': 'Tashkent'}

    def test_text_alone_no_longer_creates_a_property_and_the_refs_are_named(self, client, hotel_type, uz):
        response = client.post(URL, self.payload(hotel_type, **self.TEXT), format='json')
        assert response.status_code == 400
        for field in ('country_ref', 'region_ref'):
            assert field in details(response)
        assert not Property.objects.exists()

    def test_the_ids_decide_and_the_text_sent_with_them_is_ignored(self, client, hotel_type, uz):
        response = client.post(URL, self.payload(
            hotel_type, country_ref=uz['country'].id, region_ref=uz['samarkand'].id,
            country='Atlantis', state='Nowhere', city='Registan Town'), format='json')
        assert response.status_code == 201, response.data
        prop = Property.objects.get(address_line1='1 Main St')
        assert prop.region_ref_id == uz['samarkand'].id
        assert (prop.country, prop.state, prop.city) == ('Uzbekistan', 'Samarkand', 'Samarkand')

    def test_text_on_an_edit_changes_nothing(self, client, owner, hotel_type, uz):
        prop = Property.objects.create(
            owner=owner, property_type=hotel_type, max_guests=2, address_line1='5 Edit St', base_price=50,
            country_ref=uz['country'], region_ref=uz['tashkent'])
        prop.refresh_from_db()
        response = client.patch(f'{URL}{prop.id}/', {'city': 'Samarkand', 'country': 'Kazakhstan', 'max_guests': 3},
                                format='json')
        assert response.status_code == 200, response.data
        prop.refresh_from_db()
        assert (prop.city, prop.country, prop.max_guests) == ('Tashkent', 'Uzbekistan', 3)

    def test_the_response_shows_the_text_copies(self, client, hotel_type, uz):
        response = client.post(URL, self.payload(
            hotel_type, country_ref=uz['country'].id, region_ref=uz['tashkent'].id), format='json')
        assert response.status_code == 201, response.data
        shown = client.get(f"{URL}{Property.objects.get().id}/").data
        assert (shown['country'], shown['state'], shown['city']) == ('Uzbekistan', 'Tashkent', 'Tashkent')
