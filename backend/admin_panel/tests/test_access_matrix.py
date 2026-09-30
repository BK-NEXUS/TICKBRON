"""
Access matrix for every /api/v1/admin-panel/ endpoint.

anonymous -> 401/403, regular user -> 403, hotel owner -> 403, staff -> allowed
(super-admin only for creating hotel owners). Also: hotel owners are not
customers, and the users list reports their role.
"""
import pytest
from rest_framework.test import APIClient

from permissions.models import Role
from users.models import User

A = '/api/v1/admin-panel'

# (method, url) for every admin endpoint. Object ids do not need to exist:
# permissions are checked before the object is looked up.
ADMIN_ENDPOINTS = [
    ('get', f'{A}/'),  # router root
    ('get', f'{A}/users/'),
    ('get', f'{A}/customers/'),
    ('get', f'{A}/customers/1/'),
    ('post', f'{A}/customers/1/notes/'),
    ('put', f'{A}/customers/1/notes/1/'),
    ('delete', f'{A}/customers/1/notes/1/'),
    ('get', f'{A}/statistics/registrations/'),
    ('get', f'{A}/statistics/top-bookers/'),
    ('get', f'{A}/properties/'),
    ('get', f'{A}/properties/1/'),
    ('post', f'{A}/properties/1/approve/'),
    ('post', f'{A}/properties/1/suspend/'),
    ('patch', f'{A}/properties/1/region/'),
    ('get', f'{A}/amenities/categories/'),
    ('post', f'{A}/amenities/categories/'),
    ('get', f'{A}/amenities/categories/1/'),
    ('put', f'{A}/amenities/categories/1/'),
    ('patch', f'{A}/amenities/categories/1/'),
    ('delete', f'{A}/amenities/categories/1/'),
    ('get', f'{A}/amenities/'),
    ('post', f'{A}/amenities/'),
    ('get', f'{A}/amenities/1/'),
    ('put', f'{A}/amenities/1/'),
    ('patch', f'{A}/amenities/1/'),
    ('delete', f'{A}/amenities/1/'),
    ('get', f'{A}/payments/transactions/'),
    ('get', f'{A}/bookings/lookup/?reference_code=ABCDEF'),
    ('get', f'{A}/status/countries/'),
    ('get', f'{A}/status/countries/Uzbekistan/regions/'),
    ('get', f'{A}/status/countries/Uzbekistan/regions/Tashkent/hotels/'),
    ('get', f'{A}/status/hotels/1/'),
    ('get', f'{A}/status/users/'),
]
SUPERADMIN_ONLY = [('post', f'{A}/users/create-hotel-owner/')]
ALL_ADMIN_ENDPOINTS = ADMIN_ENDPOINTS + SUPERADMIN_ONLY


@pytest.fixture
def owner_role(db):
    role, _ = Role.objects.get_or_create(
        name='hotel-owner', defaults={'description': 'Hotel owner role', 'is_system_role': True}
    )
    return role


@pytest.fixture
def accounts(owner_role):
    return {
        'regular': User.objects.create_user(
            email='guest@example.com', password='GuestPassword#123', full_name='Demo Guest'),
        'owner': User.objects.create_user(
            email='owner@example.com', password='OwnerPassword#123', full_name='Demo Hotel Owner',
            role=owner_role),
        'staff': User.objects.create_user(
            email='staff@example.com', password='StaffPassword#123', is_staff=True),
        'superadmin': User.objects.create_superuser(
            email='admin@example.com', password='AdminPassword#123'),
    }


def call(user, method, url):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return getattr(client, method)(url, {}, format='json')


@pytest.mark.django_db
class TestAdminPanelAccessMatrix:

    @pytest.mark.parametrize('method,url', ALL_ADMIN_ENDPOINTS)
    def test_anonymous_is_rejected(self, method, url):
        assert call(None, method, url).status_code in (401, 403)

    @pytest.mark.parametrize('method,url', ALL_ADMIN_ENDPOINTS)
    def test_regular_user_gets_403(self, accounts, method, url):
        assert call(accounts['regular'], method, url).status_code == 403

    @pytest.mark.parametrize('method,url', ALL_ADMIN_ENDPOINTS)
    def test_hotel_owner_gets_403(self, accounts, method, url):
        assert call(accounts['owner'], method, url).status_code == 403

    @pytest.mark.parametrize('method,url', ADMIN_ENDPOINTS)
    def test_staff_is_let_through(self, accounts, method, url):
        # 400/404 are fine here (empty body, ids that do not exist); only 401/403 are not
        assert call(accounts['staff'], method, url).status_code not in (401, 403)

    def test_only_super_admin_creates_hotel_owners(self, accounts):
        method, url = SUPERADMIN_ONLY[0]
        assert call(accounts['staff'], method, url).status_code == 403
        assert call(accounts['superadmin'], method, url).status_code == 400  # empty body


@pytest.mark.django_db
class TestOwnersAreNotCustomers:
    """E2E: hotel owners were listed as customers and shown with role USER."""

    def test_customers_directory_lists_only_customers(self, accounts):
        response = call(accounts['staff'], 'get', f'{A}/customers/')
        names = [row['full_name'] for row in response.data['results']]
        assert names == ['Demo Guest']

    def test_customers_search_does_not_find_owners(self, accounts):
        response = call(accounts['staff'], 'get', f'{A}/customers/?search=owner')
        assert response.data['count'] == 0

    def test_users_list_reports_the_role_of_each_account(self, accounts):
        response = call(accounts['staff'], 'get', f'{A}/users/')
        by_email = {row['email']: row for row in response.data}

        assert by_email['owner@example.com']['role'] == 'hotel-owner'
        assert by_email['guest@example.com']['role'] is None
        assert by_email['admin@example.com']['is_superuser'] is True
        assert by_email['staff@example.com']['is_superuser'] is False
        # role_name stays for existing clients
        assert by_email['owner@example.com']['role_name'] == 'hotel-owner'
