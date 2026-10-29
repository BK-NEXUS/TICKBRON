"""Two-step sign-in: password, then a code from an authenticator app (or a backup code) for administrators and staff."""
import logging
from unittest import mock

import pyotp
import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from users import lockout, two_factor
from users.models import User

pytestmark = pytest.mark.django_db

PASSWORD = 'Kitob7$yy'
LOGIN = '/api/v1/auth/login/'
LOGIN_2FA = '/api/v1/auth/login/2fa/'
SETUP = '/api/v1/auth/2fa/setup/'
CONFIRM = '/api/v1/auth/2fa/confirm/'
ME = '/api/v1/auth/me/'
ADMIN_ONLY = '/api/v1/admin-panel/properties/'


NOW = 1_000_000_010.0  # 10 seconds into a 30 second step, so a test never straddles a step change


@pytest.fixture(autouse=True)
def two_factor_required(settings):
    settings.TWO_FACTOR_REQUIRED_FOR_ADMINS = True
    cache.clear()
    with mock.patch('users.two_factor._now', return_value=NOW):
        yield


def make_user(email='admin@example.com', **extra):
    return User.objects.create_user(email=email, password=PASSWORD, **extra)


def enrolled_admin(email='admin@example.com'):
    """An administrator who has finished the setup: returns the user, the app's secret and the backup codes."""
    user = make_user(email, is_staff=True, is_superuser=True)
    secret = two_factor.new_secret()
    codes = two_factor.enable(user, secret, step=0)
    return user, secret, codes


def password_step(email='admin@example.com'):
    client = APIClient()
    return client, client.post(LOGIN, {'email': email, 'password': PASSWORD}, format='json')


def send_code(client, secret, offset=0):
    return client.post(LOGIN_2FA, {'code': pyotp.TOTP(secret).at(NOW + offset)}, format='json')


class TestLoginWithTwoFactor:
    def test_the_password_alone_does_not_sign_in(self):
        enrolled_admin()
        client, response = password_step()

        assert response.status_code == 200
        assert response.data == {'two_factor_required': True}
        assert client.get(ME).status_code == 401

    def test_a_right_code_signs_in(self):
        user, secret, _ = enrolled_admin()
        client, _ = password_step()

        response = send_code(client, secret)

        assert response.status_code == 200
        assert response.data['email'] == user.email
        assert client.get(ME).status_code == 200

    def test_a_wrong_code_is_refused_without_a_session(self):
        enrolled_admin()
        client, _ = password_step()

        response = client.post(LOGIN_2FA, {'code': '000000'}, format='json')

        assert response.status_code == 401
        assert client.get(ME).status_code == 401

    def test_a_code_without_the_password_step_is_refused(self):
        _, secret, _ = enrolled_admin()

        assert send_code(APIClient(), secret).status_code == 401

    def test_the_password_step_expires_after_five_minutes(self):
        _, secret, _ = enrolled_admin()
        client, _ = password_step()

        with mock.patch('users.two_factor._now', return_value=NOW + two_factor.PENDING_SECONDS + 1):
            assert client.post(LOGIN_2FA, {'code': pyotp.TOTP(secret).at(NOW)}, format='json').status_code == 401

    def test_a_code_works_once(self):
        _, secret, _ = enrolled_admin()
        code = pyotp.TOTP(secret).at(NOW)  # one string for both tries, so a step change in between cannot matter
        first, _ = password_step()
        assert first.post(LOGIN_2FA, {'code': code}, format='json').status_code == 200

        second, _ = password_step()
        assert second.post(LOGIN_2FA, {'code': code}, format='json').status_code == 401

    def test_the_code_of_the_step_before_is_accepted_for_a_slow_phone_clock(self):
        _, secret, _ = enrolled_admin()
        client, _ = password_step()

        assert send_code(client, secret, offset=-two_factor.STEP_SECONDS).status_code == 200

    def test_a_code_two_steps_old_is_refused(self):
        _, secret, _ = enrolled_admin()
        client, _ = password_step()

        assert send_code(client, secret, offset=-3 * two_factor.STEP_SECONDS).status_code == 401

    def test_the_code_may_be_typed_with_a_space_as_the_app_shows_it(self):
        _, secret, _ = enrolled_admin()
        client, _ = password_step()
        code = pyotp.TOTP(secret).at(NOW)

        assert client.post(LOGIN_2FA, {'code': f'{code[:3]} {code[3:]}'}, format='json').status_code == 200

    def test_five_wrong_codes_lock_the_step(self):
        _, secret, _ = enrolled_admin()
        client, _ = password_step()
        for _ in range(lockout.IP_FAILURE_LIMIT):
            client.post(LOGIN_2FA, {'code': '000000'}, format='json')

        assert send_code(client, secret).status_code == 401

    def test_a_backup_code_works_once(self):
        _, _, codes = enrolled_admin()
        first, _ = password_step()
        assert first.post(LOGIN_2FA, {'backup_code': codes[0].upper()}, format='json').status_code == 200

        second, _ = password_step()
        assert second.post(LOGIN_2FA, {'backup_code': codes[0]}, format='json').status_code == 401
        third, _ = password_step()
        assert third.post(LOGIN_2FA, {'backup_code': codes[1]}, format='json').status_code == 200

    def test_the_secret_is_not_stored_as_plain_text(self):
        user, secret, codes = enrolled_admin()
        user.refresh_from_db()

        assert secret not in user.two_factor_secret
        assert two_factor.unseal(user.two_factor_secret) == secret
        assert not any(code.replace('-', '') in user.two_factor_backup_codes for code in codes)

    def test_a_guest_without_two_factor_signs_in_as_before(self):
        make_user('guest@example.com')

        _, response = password_step('guest@example.com')

        assert response.status_code == 200
        assert response.data['email'] == 'guest@example.com'

    def test_codes_and_secrets_never_reach_the_security_log(self, caplog):
        _, secret, codes = enrolled_admin()
        client, _ = password_step()
        code = pyotp.TOTP(secret).at(NOW)
        with caplog.at_level(logging.INFO, logger='tickbron.security'):
            client.post(LOGIN_2FA, {'code': '000000'}, format='json')
            client.post(LOGIN_2FA, {'code': code}, format='json')

        assert code not in caplog.text and secret not in caplog.text
        assert 'two_factor_failed' in caplog.text

    def test_the_second_step_is_throttled(self):
        enrolled_admin()
        client, _ = password_step()
        with mock.patch('users.throttles.TESTING', False):
            statuses = [client.post(LOGIN_2FA, {'code': '000000'}, format='json').status_code for _ in range(12)]

        assert statuses[-1] == 429


class TestSetup:
    def sign_in_without_two_factor(self, **extra):
        user = make_user(is_staff=True, **extra)
        client, response = password_step()
        assert response.status_code == 200
        return user, client

    def test_an_administrator_without_two_factor_may_only_set_it_up(self):
        _, client = self.sign_in_without_two_factor()

        blocked = client.get(ADMIN_ONLY)
        assert blocked.status_code == 403
        assert blocked.json()['code'] == 'two_factor_setup_required'
        assert client.get(ME).status_code == 200
        assert client.post(SETUP).status_code == 200
        assert client.post('/api/v1/auth/logout/').status_code == 200

    def test_me_tells_the_site_that_setup_is_required(self):
        _, client = self.sign_in_without_two_factor()

        assert client.get(ME).data['two_factor_setup_required'] is True

    def test_the_setup_gives_a_link_for_the_app_and_the_secret(self):
        user, client = self.sign_in_without_two_factor()

        data = client.post(SETUP).data

        assert data['otpauth_uri'].startswith('otpauth://totp/')
        assert 'issuer=TICKBRON' in data['otpauth_uri'] and data['secret'] in data['otpauth_uri']
        user.refresh_from_db()
        assert user.two_factor_enabled is False

    def test_a_right_code_switches_it_on_and_gives_ten_backup_codes_once(self):
        user, client = self.sign_in_without_two_factor()
        secret = client.post(SETUP).data['secret']

        response = client.post(CONFIRM, {'code': pyotp.TOTP(secret).at(NOW)}, format='json')

        assert response.status_code == 200
        assert len(response.data['backup_codes']) == two_factor.BACKUP_CODE_COUNT
        user.refresh_from_db()
        assert user.two_factor_enabled is True
        assert client.get(ADMIN_ONLY).status_code != 403
        assert client.get(ME).data['two_factor_setup_required'] is False

    def test_a_wrong_code_leaves_it_off(self):
        user, client = self.sign_in_without_two_factor()
        client.post(SETUP)

        response = client.post(CONFIRM, {'code': '000000'}, format='json')

        assert response.status_code == 400
        user.refresh_from_db()
        assert user.two_factor_enabled is False

    def test_confirming_without_a_setup_is_refused(self):
        _, client = self.sign_in_without_two_factor()

        assert client.post(CONFIRM, {'code': '123456'}, format='json').status_code == 400

    def test_it_cannot_be_set_up_again_while_on(self):
        _, secret, _ = enrolled_admin()
        client, _ = password_step()
        send_code(client, secret)

        assert client.post(SETUP).status_code == 400

    def test_the_other_sessions_of_the_user_end_when_it_is_switched_on(self):
        _, client = self.sign_in_without_two_factor()
        other, _ = password_step()
        assert other.get(ME).status_code == 200
        secret = client.post(SETUP).data['secret']

        client.post(CONFIRM, {'code': pyotp.TOTP(secret).at(NOW)}, format='json')

        assert other.get(ME).status_code == 401
        assert client.get(ME).status_code == 200

    def test_a_guest_may_set_it_up_and_then_needs_the_code(self):
        make_user('guest@example.com')
        client, _ = password_step('guest@example.com')
        secret = client.post(SETUP).data['secret']
        client.post(CONFIRM, {'code': pyotp.TOTP(secret).at(NOW)}, format='json')

        _, response = password_step('guest@example.com')

        assert response.data == {'two_factor_required': True}

    def test_when_the_requirement_is_off_an_administrator_works_as_before(self, settings):
        settings.TWO_FACTOR_REQUIRED_FOR_ADMINS = False
        _, client = self.sign_in_without_two_factor()

        assert client.get(ADMIN_ONLY).status_code != 403
        assert client.get(ME).data['two_factor_setup_required'] is False


class TestCodeCheck:
    def test_matches_the_rfc_6238_test_value(self):
        # RFC 6238 appendix B: secret "12345678901234567890", time 59 s -> 8 digit 94287082, 6 digit 287082
        secret = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'

        assert two_factor.matching_step(secret, '287082', now=59) == 1
        assert two_factor.matching_step(secret, '287083', now=59) is None

    def test_anything_that_is_not_six_digits_is_refused(self):
        secret = two_factor.new_secret()

        for code in ('', None, 'abcdef', '12345', '1234567'):
            assert two_factor.matching_step(secret, code) is None
