"""
N-17: every admin write is in the append-only AdminAccessLog (who, what, which id, when).

Before this, only reads of customer data, exchange rates, refund follow-ups, promotions and
no-show decisions were logged. Property approve/reject/suspend, creating hotel owners,
amenities, geography and internal notes left no trace. Only ids and non-personal facts are
stored (no names, notes, reasons or e-mails).
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from properties.models import Property, PropertyType
from users.models import User

A = '/api/v1/admin-panel'


@pytest.fixture
def staff(db):
    return User.objects.create_user(email='staff@example.com', password='x', is_staff=True)


@pytest.fixture
def superadmin(db):
    return User.objects.create_user(email='root@example.com', password='x', is_staff=True, is_superuser=True)


@pytest.fixture
def hotel(db):
    owner = User.objects.create_user(email='owner@example.com', password='x')
    return Property.objects.create(
        owner=owner, property_type=PropertyType.objects.create(name='Hotel', slug='hotel'),
        status='pending', max_guests=2, bedrooms=1, bathrooms=1, city='Tashkent', country='Uzbekistan',
        base_price=Decimal('50'), currency='USD',
    )


def _as(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _only_row(action):
    rows = AdminAccessLog.objects.filter(action=action)
    assert rows.count() == 1, f'{action}: {rows.count()} rows'
    return rows.get()


@pytest.mark.django_db
class TestPropertyModeration:
    def test_approve_is_logged_with_the_property_id(self, staff, hotel):
        response = _as(staff).post(f'{A}/properties/{hotel.id}/approve/', {}, format='json')

        assert response.status_code == 200
        row = _only_row('property_approve')
        assert (row.actor_id, row.details) == (staff.id, {'property_id': hotel.id})

    def test_reject_is_logged_without_the_reason_text(self, staff, hotel):
        response = _as(staff).post(
            f'{A}/properties/{hotel.id}/approve/', {'rejection_reason': 'Photos are missing'}, format='json'
        )

        assert response.status_code == 200
        row = _only_row('property_reject')
        assert row.details == {'property_id': hotel.id}
        assert 'Photos' not in str(row.details)

    def test_suspend_is_logged(self, staff, hotel):
        assert _as(staff).post(f'{A}/properties/{hotel.id}/suspend/', {}, format='json').status_code == 200

        assert _only_row('property_suspend').details == {'property_id': hotel.id}

    def test_region_change_is_logged(self, staff, hotel):
        response = _as(staff).patch(f'{A}/properties/{hotel.id}/region/', {'state': 'Tashkent Region'}, format='json')

        assert response.status_code == 200
        assert _only_row('property_region_update').details == {'property_id': hotel.id}

    def test_a_refused_request_writes_nothing(self, hotel):
        guest = User.objects.create_user(email='guest@example.com', password='x')

        response = _as(guest).post(f'{A}/properties/{hotel.id}/approve/', {}, format='json')

        assert response.status_code == 403
        assert not AdminAccessLog.objects.filter(action__startswith='property_').exists()


@pytest.mark.django_db
class TestHotelOwnerCreation:
    def test_creating_an_owner_is_logged_with_the_new_user_id_only(self, superadmin):
        response = _as(superadmin).post(f'{A}/users/create-hotel-owner/', {
            'email': 'newowner@example.com', 'first_name': 'New', 'last_name': 'Owner',
            'password': 'Str0ng#Pass-2026!', 'password_confirm': 'Str0ng#Pass-2026!',
        }, format='json')

        assert response.status_code == 201, response.data
        row = _only_row('hotel_owner_create')
        assert row.actor_id == superadmin.id
        assert row.target_user_id == User.objects.get(email='newowner@example.com').id
        assert row.details is None

    def test_an_invalid_request_writes_nothing(self, superadmin):
        response = _as(superadmin).post(f'{A}/users/create-hotel-owner/', {'email': 'bad'}, format='json')

        assert response.status_code == 400
        assert not AdminAccessLog.objects.filter(action='hotel_owner_create').exists()


@pytest.mark.django_db
class TestAmenities:
    def test_category_and_amenity_create_update_delete_are_logged(self, staff):
        client = _as(staff)

        category = client.post(f'{A}/amenities/categories/', {'name': 'Kitchen', 'slug': 'kitchen'}, format='json')
        assert category.status_code == 201, category.data
        category_id = category.data['id']
        assert _only_row('amenity_category_create').details == {'object_id': category_id}

        assert client.patch(f'{A}/amenities/categories/{category_id}/', {'name': 'Kitchen 2'}, format='json').status_code == 200
        assert _only_row('amenity_category_update').details == {'object_id': category_id}

        amenity = client.post(f'{A}/amenities/', {'category': category_id, 'name': 'Kettle', 'slug': 'kettle'}, format='json')
        assert amenity.status_code == 201, amenity.data
        amenity_id = amenity.data['id']
        assert _only_row('amenity_create').details == {'object_id': amenity_id}

        assert client.patch(f'{A}/amenities/{amenity_id}/', {'name': 'Kettle 2'}, format='json').status_code == 200
        assert _only_row('amenity_update').details == {'object_id': amenity_id}

        assert client.delete(f'{A}/amenities/{amenity_id}/').status_code == 204
        assert _only_row('amenity_delete').details == {'object_id': amenity_id}

        assert client.delete(f'{A}/amenities/categories/{category_id}/').status_code == 204
        assert _only_row('amenity_category_delete').details == {'object_id': category_id}


@pytest.mark.django_db
class TestGeography:
    def test_country_create_update_delete_and_reorder_are_logged_with_the_level(self, superadmin):
        client = _as(superadmin)

        created = client.post(f'{A}/geography/countries/', {
            'code': 'ZZ', 'currency': 'USD', 'name_en': 'Zedland', 'name_uz': 'Zedland', 'name_ru': 'Зедландия',
        }, format='json')
        assert created.status_code == 201, created.data
        country_id = created.data['id']
        assert _only_row('geography_create').details == {'level': 'country', 'object_id': country_id}

        assert client.patch(f'{A}/geography/countries/{country_id}/', {'is_active': False}, format='json').status_code == 200
        assert _only_row('geography_update').details == {'level': 'country', 'object_id': country_id}

        reorder = client.post(f'{A}/geography/countries/reorder/', {'ids': [country_id]}, format='json')
        assert reorder.status_code == 200
        assert _only_row('geography_reorder').details == {'level': 'country', 'rows': 1}

        assert client.delete(f'{A}/geography/countries/{country_id}/').status_code == 204
        assert _only_row('geography_delete').details == {'level': 'country', 'object_id': country_id}

    def test_a_delete_that_is_refused_because_the_row_is_in_use_writes_nothing(self, superadmin, hotel):
        from geography.models import Country

        country = Country.objects.get(code='UZ')  # loaded by the geography data migration
        Property.objects.filter(pk=hotel.pk).update(country_ref=country)

        response = _as(superadmin).delete(f'{A}/geography/countries/{country.id}/')

        assert response.status_code == 409
        assert not AdminAccessLog.objects.filter(action='geography_delete').exists()


@pytest.mark.django_db
class TestInternalNotes:
    def test_note_create_update_delete_are_logged_against_the_customer(self, staff):
        customer = User.objects.create_user(email='customer@example.com', password='x')
        client = _as(staff)

        created = client.post(f'{A}/customers/{customer.id}/notes/', {'note': 'Called the guest'}, format='json')
        assert created.status_code == 201, created.data
        note_id = created.data['id']
        row = _only_row('internal_note_create')
        assert (row.target_user_id, row.details) == (customer.id, {'object_id': note_id})
        assert 'Called' not in str(row.details)

        assert client.put(f'{A}/customers/{customer.id}/notes/{note_id}/', {'note': 'Edited'}, format='json').status_code == 200
        assert _only_row('internal_note_update').target_user_id == customer.id

        assert client.delete(f'{A}/customers/{customer.id}/notes/{note_id}/').status_code == 204
        assert _only_row('internal_note_delete').details == {'object_id': note_id}
