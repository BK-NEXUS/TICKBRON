"""
A hotel owner names and describes a hotel in uz / ru / en and edits it afterwards (PLAN_NEXT step 2).
`translations` is {language: {name, description}}; saved as PropertyTranslation rows, shown on the cards.
Default rule: name, description and address change at once, no new approval; status and place stay locked.
"""
import pytest
from rest_framework.test import APIClient

from geography.models import City
from partner.models import OwnerPlace
from partner.tests.geography_helpers import uzbek_location
from permissions.models import Role
from properties.models import Property, PropertyTranslation, PropertyType
from users.models import User

# The marker (not only the `db` fixture) puts the default exchange-rate row of conftest inside the test transaction
pytestmark = pytest.mark.django_db

URL = '/api/v1/partner/properties/'
TEXTS = {'uz': {'name': 'Oltin Vodiy', 'description': 'Shahar markazida'}, 'en': {'name': 'Golden Valley'}}


@pytest.fixture
def owner(db):
    role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'description': 'Owner', 'is_system_role': True})
    return User.objects.create_user(email='owner@example.com', password='OwnerPassword#123', role=role)


@pytest.fixture
def other_owner(owner):
    return User.objects.create_user(email='other@example.com', password='OwnerPassword#123', role=owner.role)


@pytest.fixture
def client_of(db):
    def make(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client
    return make


@pytest.fixture
def hotel_type(db):
    return PropertyType.objects.create(name='Hotel', slug='hotel')


def create_payload(hotel_type, **extra):
    return {
        'property_type': hotel_type.id, 'max_guests': 2, 'base_price': '60.00', 'currency': 'USD',
        'address_line1': '1 Amir Temur', **uzbek_location('Bukhara'), 'translations': TEXTS, **extra,
    }


def make_property(owner, hotel_type, **extra):
    return Property.objects.create(
        owner=owner, property_type=hotel_type, status='active', max_guests=2, address_line1='1 Main St',
        city='Tashkent', country='Uzbekistan', base_price=60, currency='USD', **extra,
    )


def test_create_saves_the_names_and_descriptions(owner, client_of, hotel_type):
    response = client_of(owner).post(URL, create_payload(hotel_type), format='json')
    assert response.status_code == 201, response.data
    prop = Property.objects.get(pk=response.data['id'])
    texts = {t.language: (t.name, t.description) for t in prop.translations.all()}
    assert texts == {'uz': ('Oltin Vodiy', 'Shahar markazida'), 'en': ('Golden Valley', '')}
    assert prop.status == 'draft'


def test_create_without_any_name_is_refused(owner, client_of, hotel_type):
    payload = create_payload(hotel_type)
    del payload['translations']
    response = client_of(owner).post(URL, payload, format='json')
    assert response.status_code == 400
    assert 'translations' in response.data['error']['details']
    assert Property.objects.count() == 0


@pytest.mark.parametrize('texts', [{}, {'en': {'name': '   '}}, {'en': {'description': 'no name'}}])
def test_create_needs_a_real_name(owner, client_of, hotel_type, texts):
    response = client_of(owner).post(URL, create_payload(hotel_type, translations=texts), format='json')
    assert response.status_code == 400
    assert Property.objects.count() == 0


@pytest.mark.parametrize('bad', [
    {'en': {'name': '<b>Hotel</b>'}},
    {'en': {'name': 'Hotel', 'description': '<script>alert(1)</script>'}},
    {'en': {'name': 'Hotel\x00'}},
    {'en': {'name': 'x' * 256}},
    {'en': {'name': 'Hotel', 'description': 'x' * 2001}},
    {'de': {'name': 'Hotel'}},
    {'en': 'Hotel'},
    ['en'],
])
def test_bad_texts_are_refused(owner, client_of, hotel_type, bad):
    response = client_of(owner).post(URL, create_payload(hotel_type, translations=bad), format='json')
    assert response.status_code == 400
    assert 'translations' in response.data['error']['details']
    assert Property.objects.count() == 0


def test_names_with_digits_and_punctuation_are_fine(owner, client_of, hotel_type):
    texts = {'en': {'name': "Hotel No. 7 - Samarkand's Best & Cheapest"}}
    response = client_of(owner).post(URL, create_payload(hotel_type, translations=texts), format='json')
    assert response.status_code == 201, response.data


def test_detail_returns_the_texts(owner, client_of, hotel_type):
    prop = make_property(owner, hotel_type)
    PropertyTranslation.objects.create(property=prop, language='ru', name='Отель', description='Описание')
    response = client_of(owner).get(f'{URL}{prop.id}/')
    assert response.status_code == 200
    assert response.data['translations'] == {'ru': {'name': 'Отель', 'description': 'Описание'}}


def test_patch_changes_one_language_and_keeps_the_others(owner, client_of, hotel_type):
    prop = make_property(owner, hotel_type)
    PropertyTranslation.objects.create(property=prop, language='ru', name='Отель', description='Старое')
    PropertyTranslation.objects.create(property=prop, language='en', name='Hotel', description='Old')
    response = client_of(owner).patch(
        f'{URL}{prop.id}/', {'translations': {'en': {'name': 'Hotel Plaza', 'description': 'New'}}}, format='json')
    assert response.status_code == 200, response.data
    texts = {t.language: (t.name, t.description) for t in prop.translations.all()}
    assert texts == {'ru': ('Отель', 'Старое'), 'en': ('Hotel Plaza', 'New')}
    assert response.data['name'] == 'Hotel Plaza'


def test_patch_adds_a_language_and_revives_a_deleted_one(owner, client_of, hotel_type):
    prop = make_property(owner, hotel_type)
    gone = PropertyTranslation.objects.create(property=prop, language='uz', name='Eski', description='x', is_deleted=True)
    response = client_of(owner).patch(f'{URL}{prop.id}/', {'translations': TEXTS}, format='json')
    assert response.status_code == 200, response.data
    gone.refresh_from_db()
    assert gone.is_deleted is False and gone.name == 'Oltin Vodiy'
    assert prop.translations.count() == 2


def test_edit_of_an_active_hotel_needs_no_new_approval(owner, client_of, hotel_type):
    prop = make_property(owner, hotel_type)
    response = client_of(owner).patch(
        f'{URL}{prop.id}/',
        {'translations': TEXTS, 'address_line1': '5 New Street', 'max_guests': 4}, format='json')
    assert response.status_code == 200, response.data
    prop.refresh_from_db()
    assert prop.status == 'active'
    assert prop.address_line1 == '5 New Street' and prop.max_guests == 4


def test_status_cannot_be_changed_by_the_owner(owner, client_of, hotel_type):
    prop = make_property(owner, hotel_type, )
    client_of(owner).patch(f'{URL}{prop.id}/', {'status': 'suspended'}, format='json')
    prop.refresh_from_db()
    assert prop.status == 'active'


def test_another_owners_hotel_is_404(owner, other_owner, client_of, hotel_type):
    prop = make_property(owner, hotel_type)
    response = client_of(other_owner).patch(f'{URL}{prop.id}/', {'translations': TEXTS}, format='json')
    assert response.status_code == 404
    assert prop.translations.count() == 0


def test_a_guest_is_refused(owner, client_of, hotel_type):
    guest = User.objects.create_user(email='guest@example.com', password='GuestPassword#123')
    prop = make_property(owner, hotel_type)
    assert client_of(guest).patch(f'{URL}{prop.id}/', {'translations': TEXTS}, format='json').status_code == 403
    assert APIClient().patch(f'{URL}{prop.id}/', {'translations': TEXTS}, format='json').status_code in (401, 403)
    assert prop.translations.count() == 0


def test_a_changed_place_is_still_refused(owner, client_of, hotel_type):
    bukhara = City.objects.select_related('region__country').get(region__country__code='UZ', name_en='Bukhara')
    OwnerPlace.objects.create(owner=owner, country=bukhara.region.country, region=bukhara.region, city=bukhara)
    prop = make_property(owner, hotel_type)
    other = City.objects.select_related('region__country').get(region__country__code='UZ', name_en='Samarkand')
    response = client_of(owner).patch(
        f'{URL}{prop.id}/',
        {'translations': TEXTS, 'country_ref': other.region.country_id, 'region_ref': other.region_id, 'city_ref': other.id},
        format='json')
    assert response.status_code == 400
    assert prop.translations.count() == 0


def test_the_names_show_on_the_guest_page(owner, client_of, hotel_type):
    prop = make_property(owner, hotel_type)
    client_of(owner).patch(
        f'{URL}{prop.id}/', {'translations': {'en': {'name': 'Golden Valley', 'description': 'Quiet'}}}, format='json')
    page = APIClient().get(f'/api/v1/properties/{prop.id}/', HTTP_ACCEPT_LANGUAGE='en')
    assert page.status_code == 200
    assert 'Golden Valley' in str(page.data)
