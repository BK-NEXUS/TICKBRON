"""Only a super admin or a staff admin changes a person's phone number or e-mail (a lost SIM, a closed mailbox)."""
import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth import SESSION_KEY
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from permissions.models import Role
from users.models import User

PASSWORD = 'Kitob7$yy'

pytestmark = pytest.mark.django_db


def url(user):
    return f'/api/v1/admin-panel/users/{user.id}/contact/'


def person(email, **flags):
    return User.objects.create_user(email=email, password=PASSWORD, phone_number='+998901112233', **flags)


def acting(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.fixture
def boss():
    return person('boss@example.com', is_staff=True, is_superuser=True)


@pytest.fixture
def staff():
    return person('staff@example.com', is_staff=True)


@pytest.fixture
def guest():
    return person('guest@example.com')


class TestWhoMayChange:
    @pytest.mark.parametrize('actor', ['boss', 'staff'])
    def test_super_admin_and_staff_change_a_guests_phone_and_email(self, request, actor, guest):
        api = acting(request.getfixturevalue(actor))
        response = api.patch(url(guest), {'phone_number': '+998909998877', 'email': 'New.Guest@Example.com'}, format='json')
        assert response.status_code == 200, response.data
        guest.refresh_from_db()
        assert (guest.phone_number, guest.email) == ('+998909998877', 'new.guest@example.com')

    def test_staff_changes_a_hotel_owners_contact(self, staff):
        role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
        owner = person('owner@example.com', role=role)
        assert acting(staff).patch(url(owner), {'phone_number': '+998909998877'}, format='json').status_code == 200

    def test_super_admin_changes_a_staff_admin(self, boss, staff):
        assert acting(boss).patch(url(staff), {'phone_number': '+998909998877'}, format='json').status_code == 200

    def test_staff_cannot_change_another_staff_or_a_super_admin(self, staff, boss):
        other = person('other.staff@example.com', is_staff=True)
        api = acting(staff)
        for target in (other, boss):
            assert api.patch(url(target), {'email': 'x@example.com'}, format='json').status_code == 403
            target.refresh_from_db()
            assert target.email != 'x@example.com'

    def test_nobody_changes_a_super_admin_through_the_api(self, boss):
        second = person('second.boss@example.com', is_staff=True, is_superuser=True)
        assert acting(boss).patch(url(second), {'email': 'x@example.com'}, format='json').status_code == 403

    def test_guest_owner_and_anonymous_are_refused(self, guest):
        victim = person('victim@example.com')
        assert acting(guest).patch(url(victim), {'email': 'x@example.com'}, format='json').status_code == 403
        assert APIClient().patch(url(victim), {'email': 'x@example.com'}, format='json').status_code in (401, 403)
        victim.refresh_from_db()
        assert victim.email == 'victim@example.com'

    def test_a_deleted_or_unknown_account_is_404(self, boss):
        gone = person('gone@example.com')
        User.objects.filter(pk=gone.pk).update(is_deleted=True)
        assert acting(boss).patch(url(gone), {'email': 'x@example.com'}, format='json').status_code == 404
        assert acting(boss).patch('/api/v1/admin-panel/users/999999/contact/', {'email': 'x@example.com'}, format='json').status_code == 404


class TestWhatIsChecked:
    @pytest.mark.parametrize('payload, field', [
        ({'email': 'not-an-email'}, 'email'),
        ({'phone_number': 'abc'}, 'phone_number'),
        ({'phone_number': ''}, 'phone_number'),
        ({'email': 'boss@example.com'}, 'email'),
        ({'email': 'BOSS@example.com'}, 'email'),
    ])
    def test_bad_input_is_refused_with_the_field_named(self, boss, guest, payload, field):
        response = acting(boss).patch(url(guest), payload, format='json')
        assert response.status_code == 400
        assert field in response.data

    def test_an_empty_request_is_refused(self, boss, guest):
        assert acting(boss).patch(url(guest), {}, format='json').status_code == 400

    def test_the_same_email_in_other_case_is_the_accounts_own_not_a_clash(self, boss, guest):
        assert acting(boss).patch(url(guest), {'email': 'GUEST@example.com'}, format='json').status_code == 200

    def test_other_fields_in_the_request_are_ignored(self, boss, guest):
        acting(boss).patch(url(guest), {'phone_number': '+998909998877', 'is_staff': True, 'is_superuser': True}, format='json')
        guest.refresh_from_db()
        assert (guest.is_staff, guest.is_superuser) == (False, False)

    def test_a_non_object_body_is_a_400_not_a_500(self, boss, guest):
        assert acting(boss).patch(url(guest), ['x'], format='json').status_code == 400


class TestWhatFollows:
    def test_the_change_is_written_to_the_access_log_without_the_values(self, boss, guest):
        acting(boss).patch(url(guest), {'phone_number': '+998909998877', 'email': 'new.guest@example.com'}, format='json')
        row = AdminAccessLog.objects.get(action='user_contact_update')
        assert (row.actor_id, row.target_user_id) == (boss.id, guest.id)
        assert row.details == {'fields': 'email,phone_number'}
        assert '998909998877' not in str(row.details) and 'new.guest' not in str(row.details)

    def test_a_change_of_email_signs_the_person_out_everywhere(self, boss, guest):
        session = SessionStore()
        session[SESSION_KEY] = str(guest.pk)
        session.create()
        acting(boss).patch(url(guest), {'email': 'new.guest@example.com'}, format='json')
        assert not SessionStore(session_key=session.session_key).exists(session.session_key)

    def test_a_change_of_phone_only_keeps_the_sessions(self, boss, guest):
        session = SessionStore()
        session[SESSION_KEY] = str(guest.pk)
        session.create()
        acting(boss).patch(url(guest), {'phone_number': '+998909998877'}, format='json')
        assert SessionStore(session_key=session.session_key).exists(session.session_key)

    def test_a_change_of_email_marks_it_unverified(self, boss, guest):
        User.objects.filter(pk=guest.pk).update(email_verified=True)
        acting(boss).patch(url(guest), {'email': 'new.guest@example.com'}, format='json')
        guest.refresh_from_db()
        assert guest.email_verified is False

    def test_the_answer_shows_the_account_without_secrets(self, boss, guest):
        response = acting(boss).patch(url(guest), {'phone_number': '+998909998877'}, format='json')
        assert response.data['phone_number'] == '+998909998877'
        assert 'password' not in response.data and 'two_factor_secret' not in response.data
