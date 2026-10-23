"""
The place of a hotel-owner account (plan .ai/PLAN_GEO_IMAGES.md, step 3): the super admin picks
country > region > city when creating the account; the owner's hotels are created in that place and
cannot be moved by the owner.
"""
import pytest
from rest_framework.test import APIClient

from geography.models import City, Country, Region
from partner.models import OwnerPlace
from permissions.models import Role
from properties.models import Property, PropertyType
from users.models import User

CREATE = '/api/v1/admin-panel/users/create-hotel-owner/'
PLACE = '/api/v1/partner/assigned-place/'
PROPERTIES = '/api/v1/partner/properties/'


def details(response):
    return response.data['error']['details'] if 'error' in response.data else response.data


@pytest.fixture
def admin(db):
    return User.objects.create_superuser(email='admin@example.com', password='AdminPassword#123')


@pytest.fixture
def admin_client(admin):
    api = APIClient()
    api.force_authenticate(user=admin)
    return api


@pytest.fixture
def world(db):
    country = Country.objects.create(code='XA', name_uz='Xland', name_ru='Иксландия', name_en='Xland', currency='USD')
    east = Region.objects.create(country=country, name_uz='Sharq', name_ru='Восток', name_en='East')
    west = Region.objects.create(country=country, name_uz="G'arb", name_ru='Запад', name_en='West')
    capital = City.objects.create(region=east, name_uz='Poytaxt', name_ru='Столица', name_en='Capital')
    harbour = City.objects.create(region=west, name_uz='Port', name_ru='Порт', name_en='Harbour')
    other = Country.objects.create(code='XB', name_uz='Yland', name_ru='Игрекландия', name_en='Yland', currency='USD')
    south = Region.objects.create(country=other, name_uz='Janub', name_ru='Юг', name_en='South')
    return {'country': country, 'east': east, 'west': west, 'capital': capital, 'harbour': harbour, 'south': south}


def account(world, **overrides):
    body = {
        'email': 'newowner@example.com', 'first_name': 'Hotel', 'last_name': 'Owner',
        'phone_number': '+998901234567', 'password': 'Owner#Secret2026', 'password_confirm': 'Owner#Secret2026',
        'country_ref': world['country'].id, 'region_ref': world['east'].id, 'city_ref': world['capital'].id,
    }
    body.update(overrides)
    return body


def place_of(world, region='east', city='capital'):
    return {'country_ref': world['country'].id, 'region_ref': world[region].id, 'city_ref': world[city].id}


@pytest.fixture
def owner(db, world):
    role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'description': 'Hotel owner', 'is_system_role': True})
    user = User.objects.create_user(email='owner@example.com', password='OwnerPassword#123', role=role)
    OwnerPlace.objects.create(owner=user, country=world['country'], region=world['east'], city=world['capital'])
    return user


@pytest.fixture
def owner_client(owner):
    api = APIClient()
    api.force_authenticate(user=owner)
    return api


@pytest.fixture
def hotel_type(db):
    return PropertyType.objects.create(name='Hotel', slug='hotel')


def property_body(hotel_type, **location):
    return {'property_type': hotel_type.id, 'max_guests': 2, 'bedrooms': 1, 'bathrooms': 1, 'address_line1': '1 Main St',
            'translations': {'en': {'name': 'Test Hotel'}}, 'base_price': '70.00', 'currency': 'USD', **location}


@pytest.mark.django_db
class TestAdminCreatesAccountWithAPlace:
    def test_account_and_place_are_created_together(self, admin_client, world):
        response = admin_client.post(CREATE, account(world), format='json')
        assert response.status_code == 201, response.data
        user = User.objects.get(email='newowner@example.com')
        assert user.role.name == 'hotel-owner'
        place = OwnerPlace.objects.get(owner=user)
        assert (place.country_id, place.region_id, place.city_id) == (world['country'].id, world['east'].id, world['capital'].id)

    @pytest.mark.parametrize('missing', ['country_ref', 'region_ref', 'city_ref'])
    def test_the_place_is_required_and_nothing_is_created_without_it(self, admin_client, world, missing):
        body = account(world)
        del body[missing]
        response = admin_client.post(CREATE, body, format='json')
        assert response.status_code == 400
        assert missing in details(response)
        assert not User.objects.filter(email='newowner@example.com').exists()
        assert OwnerPlace.objects.count() == 0

    def test_a_region_of_another_country_is_refused_and_creates_nothing(self, admin_client, world):
        response = admin_client.post(CREATE, account(world, region_ref=world['south'].id), format='json')
        assert response.status_code == 400
        assert 'region_ref' in details(response)
        assert not User.objects.filter(email='newowner@example.com').exists()

    def test_a_city_of_another_region_is_refused(self, admin_client, world):
        response = admin_client.post(CREATE, account(world, city_ref=world['harbour'].id), format='json')
        assert response.status_code == 400
        assert 'city_ref' in details(response)

    def test_a_hidden_place_cannot_be_chosen(self, admin_client, world):
        City.objects.filter(pk=world['capital'].pk).update(is_active=False)
        response = admin_client.post(CREATE, account(world), format='json')
        assert response.status_code == 400
        assert 'city_ref' in details(response)

    def test_staff_cannot_create_accounts(self, world):
        staff_role, _ = Role.objects.get_or_create(name='staff', defaults={'is_system_role': True})
        staff = User.objects.create_user(email='staff@example.com', password='StaffPassword#123', role=staff_role, is_staff=True)
        api = APIClient()
        api.force_authenticate(user=staff)
        assert api.post(CREATE, account(world), format='json').status_code == 403
        assert OwnerPlace.objects.count() == 0

    def test_a_place_in_use_by_an_account_cannot_be_deleted_only_hidden(self, admin_client, owner, world):
        response = admin_client.delete(f'/api/v1/admin-panel/geography/cities/{world["capital"].id}/')
        assert response.status_code == 409
        assert City.objects.filter(pk=world['capital'].pk).exists()


@pytest.mark.django_db
class TestOwnerSeesAndKeepsThePlace:
    def test_assigned_place_endpoint(self, owner_client, world):
        response = owner_client.get(PLACE)
        assert response.status_code == 200
        assert response.data == place_of(world)

    def test_an_owner_without_a_place_gets_nulls(self, world):
        role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
        free = User.objects.create_user(email='free@example.com', password='OwnerPassword#123', role=role)
        api = APIClient()
        api.force_authenticate(user=free)
        assert api.get(PLACE).data == {'country_ref': None, 'region_ref': None, 'city_ref': None}

    def test_guests_and_anonymous_cannot_read_it(self, world):
        assert APIClient().get(PLACE).status_code in (401, 403)
        guest = User.objects.create_user(email='guest@example.com', password='GuestPassword#123')
        api = APIClient()
        api.force_authenticate(user=guest)
        assert api.get(PLACE).status_code == 403

    def test_a_hotel_can_be_created_in_the_assigned_place(self, owner_client, hotel_type, world):
        response = owner_client.post(PROPERTIES, property_body(hotel_type, **place_of(world)), format='json')
        assert response.status_code == 201, response.data

    @pytest.mark.parametrize('region,city', [('west', 'harbour'), ('east', 'harbour')])
    def test_a_hotel_elsewhere_is_refused(self, owner_client, hotel_type, world, region, city):
        response = owner_client.post(PROPERTIES, property_body(hotel_type, **place_of(world, region, city)), format='json')
        assert response.status_code == 400
        assert Property.objects.count() == 0

    def test_the_place_of_an_existing_hotel_cannot_be_changed_by_the_owner(self, owner_client, owner, hotel_type, world):
        assert owner_client.post(PROPERTIES, property_body(hotel_type, **place_of(world)), format='json').status_code == 201
        hotel = Property.objects.get(owner=owner)
        url = f'{PROPERTIES}{hotel.id}/'
        moved = owner_client.patch(url, place_of(world, 'west', 'harbour'), format='json')
        assert moved.status_code == 400
        assert Property.objects.get(pk=hotel.pk).city_ref_id == world['capital'].id
        assert owner_client.patch(url, {'bedrooms': 3}, format='json').status_code == 200
        same = owner_client.patch(url, place_of(world), format='json')
        assert same.status_code == 200
