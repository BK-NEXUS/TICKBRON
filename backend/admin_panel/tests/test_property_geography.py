"""
Admins fix a property's location with geography refs (Geography plan G4, city level removed 2026-11-10):
PATCH /api/v1/admin-panel/properties/{id}/region/ with country_ref, region_ref.
The old { "state": "..." } body keeps working until the frontend has moved.
Access (staff only) is covered by test_access_matrix.py.
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from geography.models import Country, Region
from properties.models import Property, PropertyType
from users.models import User


@pytest.fixture
def staff(db):
    return User.objects.create_user(email='staff@example.com', password='StaffPassword#123', is_staff=True)


@pytest.fixture
def world(db):
    xland = Country.objects.create(code='XA', name_uz='Xland', name_ru='Иксландия', name_en='Xland', currency='USD')
    east = Region.objects.create(country=xland, name_uz='Sharq', name_ru='Восток', name_en='East')
    west = Region.objects.create(country=xland, name_uz="G'arb", name_ru='Запад', name_en='West')
    yland = Country.objects.create(code='XB', name_uz='Yland', name_ru='Игрекландия', name_en='Yland', currency='USD')
    south = Region.objects.create(country=yland, name_uz='Janub', name_ru='Юг', name_en='South')
    return {'xland': xland, 'east': east, 'west': west, 'yland': yland, 'south': south}


@pytest.fixture
def prop(db):
    owner = User.objects.create_user(email='owner@example.com', password='OwnerPassword#123')
    hotel_type = PropertyType.objects.create(name='Hotel', slug='hotel')
    return Property.objects.create(
        owner=owner, property_type=hotel_type, max_guests=2, address_line1='1 Main Street',
        city='Chirchiq', country='Uzbekistan', base_price=Decimal('50.00'),
    )


def patch(user, prop_id, data):
    client = APIClient()
    client.force_authenticate(user=user)
    return client.patch(f'/api/v1/admin-panel/properties/{prop_id}/region/', data, format='json')


def refs(*rows):
    return dict(zip(('country_ref', 'region_ref'), (row.id for row in rows)))


@pytest.mark.django_db
class TestAdminSetsGeography:

    def test_sets_both_and_syncs_the_text_fields_and_leaves_the_town(self, staff, prop, world):
        response = patch(staff, prop.id, refs(world['xland'], world['east']))
        assert response.status_code == 200, response.data
        assert (response.data['country_ref'], response.data['region_ref']) == (world['xland'].id, world['east'].id)
        assert 'city_ref' not in response.data
        prop.refresh_from_db()
        assert (prop.country, prop.state, prop.city) == ('Xland', 'East', 'Chirchiq')

    def test_the_admin_can_fix_the_country_too(self, staff, prop, world):
        patch(staff, prop.id, refs(world['xland'], world['east']))
        response = patch(staff, prop.id, refs(world['yland'], world['south']))
        assert response.status_code == 200, response.data
        prop.refresh_from_db()
        assert (prop.country_ref_id, prop.region_ref_id) == (world['yland'].id, world['south'].id)

    def test_null_for_both_clears_the_location(self, staff, prop, world):
        patch(staff, prop.id, refs(world['xland'], world['east']))
        response = patch(staff, prop.id, {'country_ref': None, 'region_ref': None})
        assert response.status_code == 200, response.data
        prop.refresh_from_db()
        assert (prop.country_ref_id, prop.region_ref_id, prop.state) == (None, None, None)

    def test_partial_null_is_400(self, staff, prop, world):
        patch(staff, prop.id, refs(world['xland'], world['east']))
        assert patch(staff, prop.id, {'region_ref': None}).status_code == 400

    def test_mismatching_rows_are_400_and_nothing_changes(self, staff, prop, world):
        response = patch(staff, prop.id, refs(world['xland'], world['south']))
        assert response.status_code == 400
        prop.refresh_from_db()
        assert prop.country_ref_id is None and prop.country == 'Uzbekistan'

    def test_hidden_rows_cannot_be_chosen(self, staff, prop, world):
        Region.objects.filter(pk=world['east'].pk).update(is_active=False)
        assert patch(staff, prop.id, refs(world['xland'], world['east'])).status_code == 400

    def test_partial_body_is_merged_with_the_current_location(self, staff, prop, world):
        patch(staff, prop.id, refs(world['xland'], world['east']))
        # the new region is in the same country, so the country can stay out of the body
        response = patch(staff, prop.id, {'region_ref': world['west'].id})
        assert response.status_code == 200, response.data
        prop.refresh_from_db()
        assert prop.state == 'West'

    def test_the_legacy_state_body_still_works(self, staff, prop):
        response = patch(staff, prop.id, {'state': '  Tashkent Region '})
        assert response.status_code == 200
        prop.refresh_from_db()
        assert prop.state == 'Tashkent Region'

    def test_the_property_detail_shows_the_refs(self, staff, prop, world):
        patch(staff, prop.id, refs(world['xland'], world['east']))
        client = APIClient()
        client.force_authenticate(user=staff)
        detail = client.get(f'/api/v1/admin-panel/properties/{prop.id}/')
        assert detail.status_code == 200
        assert (detail.data['country_ref'], detail.data['region_ref']) == (world['xland'].id, world['east'].id)
        assert 'city_ref' not in detail.data
