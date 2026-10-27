"""A super-admin adds another administrator (staff, not super-admin) from the panel; plan .ai/PLAN_ADMIN_ACCOUNTS.md."""
import pytest
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from permissions.models import Role
from users.models import User

URL = '/api/v1/admin-panel/users/create-admin/'
PASSWORD = 'Long-Enough-Pass#2026'


def body(**extra):
    return {'email': 'new.admin@example.com', 'first_name': 'Aziza', 'last_name': 'Karimova',
            'phone_number': '+998901234567', 'password': PASSWORD, 'password_confirm': PASSWORD, **extra}


def client_of(**flags):
    user = User.objects.create_user(email=f"u{User.objects.count()}@example.com", password=PASSWORD, **flags)
    api = APIClient()
    api.force_authenticate(user=user)
    return api, user


@pytest.mark.django_db
class TestCreateAdmin:
    def test_super_admin_creates_a_staff_account_that_is_not_super_admin(self):
        api, boss = client_of(is_staff=True, is_superuser=True)
        response = api.post(URL, body(), format='json')
        assert response.status_code == 201, response.data
        created = User.objects.get(email='new.admin@example.com')
        assert (created.is_staff, created.is_superuser, created.is_active) == (True, False, True)
        assert created.check_password(PASSWORD)
        assert 'password' not in response.data

    def test_a_rights_flag_in_the_body_is_ignored(self):
        api, _ = client_of(is_staff=True, is_superuser=True)
        api.post(URL, body(is_superuser=True), format='json')
        assert User.objects.get(email='new.admin@example.com').is_superuser is False

    def test_the_creation_is_written_to_the_access_log(self):
        api, boss = client_of(is_staff=True, is_superuser=True)
        api.post(URL, body(), format='json')
        created = User.objects.get(email='new.admin@example.com')
        row = AdminAccessLog.objects.get(action='admin_create')
        assert (row.actor_id, row.target_user_id) == (boss.id, created.id)

    @pytest.mark.parametrize('flags', [
        {'is_staff': True}, {}, {'is_staff': False, 'is_superuser': False},
    ])
    def test_staff_guest_and_owner_cannot_create_one(self, flags):
        api, _ = client_of(**flags)
        assert api.post(URL, body(), format='json').status_code == 403
        assert not User.objects.filter(email='new.admin@example.com').exists()

    def test_the_hotel_owner_cannot_create_one(self):
        role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
        api, _ = client_of(role=role)
        assert api.post(URL, body(), format='json').status_code == 403

    def test_anonymous_is_refused(self):
        assert APIClient().post(URL, body(), format='json').status_code in (401, 403)

    @pytest.mark.parametrize('change, field', [
        ({'password': 'short', 'password_confirm': 'short'}, 'password'),
        ({'password_confirm': 'Different-Pass#2026'}, 'password_confirm'),
        ({'email': 'not-an-email'}, 'email'),
        ({'phone_number': 'abc'}, 'phone_number'),
        ({'first_name': '<b>x</b>'}, 'first_name'),
    ])
    def test_bad_input_is_refused_with_the_field_named(self, change, field):
        api, _ = client_of(is_staff=True, is_superuser=True)
        response = api.post(URL, body(**change), format='json')
        assert response.status_code == 400
        assert field in response.data

    def test_a_used_email_is_refused(self):
        api, boss = client_of(is_staff=True, is_superuser=True)
        response = api.post(URL, body(email=boss.email), format='json')
        assert response.status_code == 400
        assert 'email' in response.data
