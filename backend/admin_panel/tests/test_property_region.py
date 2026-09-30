"""
Admins set a property's region (Status plan S1):
PATCH /api/v1/admin-panel/properties/{id}/region/ with { "state": "..." }.
Access (staff only) is covered by test_access_matrix.py.
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from properties.models import Property, PropertyType
from users.models import User


@pytest.fixture
def staff(db):
    return User.objects.create_user(email='staff@example.com', password='StaffPassword#123', is_staff=True)


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


@pytest.mark.django_db
class TestAdminSetsPropertyRegion:

    def test_sets_the_region(self, staff, prop):
        response = patch(staff, prop.id, {'state': '  Tashkent Region '})

        assert response.status_code == 200
        assert response.data['state'] == 'Tashkent Region'
        prop.refresh_from_db()
        assert prop.state == 'Tashkent Region'

    def test_blank_clears_the_region(self, staff, prop):
        prop.state = 'Tashkent Region'
        prop.save()

        response = patch(staff, prop.id, {'state': ''})

        assert response.status_code == 200
        prop.refresh_from_db()
        assert prop.state is None

    def test_changes_nothing_else(self, staff, prop):
        response = patch(staff, prop.id, {'state': 'Tashkent Region', 'city': 'Elsewhere', 'status': 'active'})

        assert response.status_code == 200
        prop.refresh_from_db()
        assert (prop.city, prop.status) == ('Chirchiq', 'draft')

    def test_rejects_a_region_longer_than_the_column(self, staff, prop):
        assert patch(staff, prop.id, {'state': 'x' * 101}).status_code == 400

    def test_requires_the_state_field(self, staff, prop):
        assert patch(staff, prop.id, {}).status_code == 400

    def test_unknown_property_is_404(self, staff):
        assert patch(staff, 999999, {'state': 'Tashkent'}).status_code == 404
