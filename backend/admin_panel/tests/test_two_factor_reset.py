"""A super admin resets another account's two-step sign-in (a lost phone) with their own current code; plan .ai/PLAN_2FA.md."""
from io import StringIO
from unittest import mock

import pyotp
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient

from accounts.models import Notification
from admin_panel.models import AdminAccessLog
from users import two_factor
from users.models import User

pytestmark = pytest.mark.django_db

PASSWORD = 'Kitob7$yy'
NOW = 1_000_000_010.0


@pytest.fixture(autouse=True)
def frozen_clock():
    with mock.patch('users.two_factor._now', return_value=NOW):
        yield


def url(user):
    return f'/api/v1/admin-panel/users/{user.id}/2fa-reset/'


def person(email, enrolled=False, **flags):
    user = User.objects.create_user(email=email, password=PASSWORD, **flags)
    secret = None
    if enrolled:
        secret = two_factor.new_secret()
        two_factor.enable(user, secret, step=0)
    return user, secret


def signed_in(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


def own_code(secret):
    return pyotp.TOTP(secret).at(NOW)


@pytest.fixture
def boss():
    return person('boss@example.com', enrolled=True, is_staff=True, is_superuser=True)


@pytest.fixture
def lost_phone():
    return person('moderator@example.com', enrolled=True, is_staff=True)[0]


class TestReset:
    def test_it_switches_the_target_s_two_factor_off_and_clears_what_it_stored(self, boss, lost_phone):
        boss_user, boss_secret = boss

        response = signed_in(boss_user).post(url(lost_phone), {'code': own_code(boss_secret)}, format='json')

        assert response.status_code == 200, response.data
        lost_phone.refresh_from_db()
        assert lost_phone.two_factor_enabled is False
        stored = (lost_phone.two_factor_secret, lost_phone.two_factor_backup_codes, lost_phone.two_factor_last_step)
        assert stored == (None, None, None)

    def test_the_account_is_sent_to_the_setup_page_again_at_its_next_sign_in(self, boss, lost_phone, settings):
        settings.TWO_FACTOR_REQUIRED_FOR_ADMINS = True
        boss_user, boss_secret = boss
        signed_in(boss_user).post(url(lost_phone), {'code': own_code(boss_secret)}, format='json')

        lost_phone.refresh_from_db()
        assert two_factor.needs_setup(lost_phone) is True

    def test_the_target_is_signed_out_everywhere(self, boss, lost_phone):
        boss_user, boss_secret = boss
        victim = APIClient()
        victim.force_login(lost_phone)
        assert victim.get('/api/v1/auth/me/').status_code == 200

        signed_in(boss_user).post(url(lost_phone), {'code': own_code(boss_secret)}, format='json')

        assert victim.get('/api/v1/auth/me/').status_code == 401

    def test_other_people_s_sessions_stay(self, boss, lost_phone):
        boss_user, boss_secret = boss
        bystander, _ = person('bystander@example.com')
        other = APIClient()
        other.force_login(bystander)

        signed_in(boss_user).post(url(lost_phone), {'code': own_code(boss_secret)}, format='json')

        assert other.get('/api/v1/auth/me/').status_code == 200

    def test_it_is_written_to_the_access_log_without_any_secret(self, boss, lost_phone):
        boss_user, boss_secret = boss

        signed_in(boss_user).post(url(lost_phone), {'code': own_code(boss_secret)}, format='json')

        row = AdminAccessLog.objects.get(action='two_factor_reset')
        assert (row.actor_id, row.target_user_id, row.details) == (boss_user.id, lost_phone.id, None)

    def test_the_account_gets_a_notice(self, boss, lost_phone):
        boss_user, boss_secret = boss

        signed_in(boss_user).post(url(lost_phone), {'code': own_code(boss_secret)}, format='json')

        assert Notification.objects.filter(user=lost_phone, code='two_factor_reset').count() == 1


class TestRefusals:
    def test_a_wrong_own_code_changes_nothing(self, boss, lost_phone):
        response = signed_in(boss[0]).post(url(lost_phone), {'code': '000000'}, format='json')

        assert response.status_code == 400
        lost_phone.refresh_from_db()
        assert lost_phone.two_factor_enabled is True
        assert not AdminAccessLog.objects.filter(action='two_factor_reset').exists()

    def test_no_code_changes_nothing(self, boss, lost_phone):
        assert signed_in(boss[0]).post(url(lost_phone), {}, format='json').status_code == 400

    def test_the_super_admin_s_code_works_once(self, boss, lost_phone):
        boss_user, boss_secret = boss
        second, _ = person('second@example.com', enrolled=True, is_staff=True)
        code = own_code(boss_secret)
        api = signed_in(boss_user)

        assert api.post(url(lost_phone), {'code': code}, format='json').status_code == 200
        assert api.post(url(second), {'code': code}, format='json').status_code == 400

    def test_a_super_admin_without_two_factor_of_their_own_cannot_reset_anybody(self, lost_phone):
        bare, _ = person('bare@example.com', is_staff=True, is_superuser=True)

        assert signed_in(bare).post(url(lost_phone), {'code': '123456'}, format='json').status_code == 400

    def test_a_super_admin_s_two_factor_cannot_be_reset_through_the_api(self, boss):
        boss_user, boss_secret = boss
        other_boss, _ = person('boss2@example.com', enrolled=True, is_staff=True, is_superuser=True)

        response = signed_in(boss_user).post(url(other_boss), {'code': own_code(boss_secret)}, format='json')

        assert response.status_code == 403
        other_boss.refresh_from_db()
        assert other_boss.two_factor_enabled is True

    def test_an_account_without_two_factor_has_nothing_to_reset(self, boss):
        boss_user, boss_secret = boss
        plain, _ = person('plain@example.com', is_staff=True)

        assert signed_in(boss_user).post(url(plain), {'code': own_code(boss_secret)}, format='json').status_code == 400

    def test_an_unknown_account_is_not_found(self, boss):
        boss_user, boss_secret = boss

        response = signed_in(boss_user).post(
            '/api/v1/admin-panel/users/999999/2fa-reset/', {'code': own_code(boss_secret)}, format='json')

        assert response.status_code == 404

    @pytest.mark.parametrize('flags', [{'is_staff': True}, {}])
    def test_staff_and_guests_cannot_reset_anybody(self, lost_phone, flags):
        user, secret = person('someone@example.com', enrolled=True, **flags)

        response = signed_in(user).post(url(lost_phone), {'code': own_code(secret)}, format='json')

        assert response.status_code == 403
        lost_phone.refresh_from_db()
        assert lost_phone.two_factor_enabled is True

    def test_nobody_signed_out_is_let_in(self, lost_phone):
        assert APIClient().post(url(lost_phone), {'code': '123456'}, format='json').status_code in (401, 403)


class TestServerCommand:
    def run(self, email):
        out = StringIO()
        call_command('reset_2fa', email, stdout=out)
        return out.getvalue()

    def test_it_resets_any_account_including_a_super_admin(self, boss):
        boss_user, _ = boss

        text = self.run('BOSS@example.com')

        boss_user.refresh_from_db()
        assert boss_user.two_factor_enabled is False
        assert boss_user.two_factor_secret is None
        assert 'reset' in text.lower()

    def test_it_ends_the_account_s_sessions(self, boss):
        boss_user, _ = boss
        client = APIClient()
        client.force_login(boss_user)

        self.run('boss@example.com')

        assert client.get('/api/v1/auth/me/').status_code == 401

    def test_it_says_when_the_account_does_not_exist(self):
        with pytest.raises(CommandError):
            self.run('nobody@example.com')

    def test_it_says_when_there_is_nothing_to_reset(self):
        person('plain@example.com')

        assert 'not on' in self.run('plain@example.com')
