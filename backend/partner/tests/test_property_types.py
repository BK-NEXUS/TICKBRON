"""The owner's "add a hotel" form needs every property type, also the ones that have no hotel yet."""
import pytest
from rest_framework.test import APIClient

from permissions.models import Role
from properties.models import PropertyType
from users.models import User

URL = '/api/v1/partner/property-types/'

# The marker (not only the `db` fixture) puts the test in its transaction before conftest's default exchange rate is
# written; without it the rate stays in the database and breaks the "no rate yet" search tests that run later
pytestmark = pytest.mark.django_db


@pytest.fixture
def owner_client(db):
    role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
    api = APIClient()
    api.force_authenticate(user=User.objects.create_user(email='o@example.com', password='OwnerPassword#123', role=role))
    return api


def test_lists_all_types_by_name_even_without_hotels(owner_client):
    PropertyType.objects.create(name='Hotel', slug='hotel')
    PropertyType.objects.create(name='Apartment', slug='apartment')
    gone = PropertyType.objects.create(name='Old', slug='old')
    gone.soft_delete()
    response = owner_client.get(URL)
    assert response.status_code == 200
    assert [row['name'] for row in response.json()] == ['Apartment', 'Hotel']
    assert set(response.json()[0]) == {'id', 'name', 'slug'}


def test_a_guest_cannot_use_it(db):
    role, _ = Role.objects.get_or_create(name='customer', defaults={'is_system_role': True})
    api = APIClient()
    api.force_authenticate(user=User.objects.create_user(email='g@example.com', password='GuestPassword#123', role=role))
    assert api.get(URL).status_code == 403


def test_anonymous_gets_401_or_403(db):
    assert APIClient().get(URL).status_code in (401, 403)
