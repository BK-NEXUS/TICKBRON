"""
OWASP 2025 A09: security events are recorded where an investigator can find them.

Before: logins, failures, lockouts, logouts and registrations left no trace; refused requests
(401/403/429) were logged without who, from where or which URL; production dropped INFO lines
and several modules logged to stdout only; staff actions had no source address.
"""
import logging
from unittest import mock

import pytest
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient

from accounts.models import AccountHistory
from admin_panel.models import AdminAccessLog
from config.logging_config import get_logging_config
from users.models import User

PASSWORD = 'Str0ng#Pass-2026!'
EMAIL = 'victim@example.com'
PHONE = '+998901234567'


@pytest.fixture(autouse=True)
def _clean_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def security(caplog):
    caplog.set_level(logging.INFO, logger='tickbron.security')
    return caplog


def _events(caplog, name=None):
    lines = [r.getMessage() for r in caplog.records if r.name == 'tickbron.security']
    return [line for line in lines if name is None or f'event={name} ' in line + ' ']


@pytest.fixture
def user(db):
    return User.objects.create_user(email=EMAIL, password=PASSWORD, phone_number=PHONE)


def _login(password=PASSWORD, email=EMAIL):
    return APIClient().post('/api/v1/auth/login/', {'email': email, 'password': password}, format='json')


class TestLoggingConfiguration:
    @pytest.mark.parametrize('debug', [True, False])
    def test_security_events_are_always_kept_at_info_in_a_file(self, debug):
        with override_settings(DEBUG=debug):
            config = get_logging_config()

        security = config['loggers']['tickbron.security']
        assert security['level'] == 'INFO'
        assert 'security_file' in security['handlers']
        assert config['handlers']['security_file']['level'] == 'INFO'

    def test_module_loggers_reach_a_file_not_only_stdout(self):
        with override_settings(DEBUG=False):
            config = get_logging_config()

        assert 'file' in config['root']['handlers']


@pytest.mark.django_db
class TestAccountEvents:
    def test_a_successful_login_is_recorded_with_the_account_and_the_address(self, user, security):
        assert _login().status_code == 200

        [line] = _events(security, 'login_success')
        assert f'user={user.id}' in line and 'ip=127.0.0.1' in line
        row = AccountHistory.objects.get(user=user, action='login')
        assert row.ip_address == '127.0.0.1'

    def test_a_wrong_password_is_recorded_without_the_password_or_email(self, user, security):
        assert _login(password='wrong-password-123').status_code == 401

        [line] = _events(security, 'login_failed')
        assert f'user={user.id}' in line and 'reason=bad_credentials' in line
        assert 'wrong-password-123' not in line and EMAIL not in line

    def test_an_unknown_account_is_recorded_without_the_email(self, security):
        assert _login(email='nobody@example.com').status_code == 401

        [line] = _events(security, 'login_failed')
        assert 'reason=unknown_account' in line and 'user=none' in line
        assert 'nobody@example.com' not in line

    def test_a_lockout_is_recorded_once_and_later_attempts_say_locked(self, user, security):
        for _ in range(5):
            _login(password='wrong-password-123')
        _login(password='wrong-password-123')

        assert len(_events(security, 'lockout')) == 1
        assert 'reason=locked' in _events(security, 'login_failed')[-1]

    def test_logout_is_recorded(self, user, security):
        client = APIClient()
        client.post('/api/v1/auth/login/', {'email': EMAIL, 'password': PASSWORD}, format='json')

        client.post('/api/v1/auth/logout/', {}, format='json')

        assert len(_events(security, 'logout')) == 1
        assert AccountHistory.objects.filter(user=user, action='logout').exists()

    def test_registration_is_recorded(self, db, security):
        response = APIClient().post('/api/v1/auth/register/', {
            'email': 'new@example.com', 'full_name': 'New User', 'phone_number': '+998901112288',
            'password': PASSWORD, 'password_confirm': PASSWORD}, format='json')

        assert response.status_code == 201
        new_user = User.objects.get(email='new@example.com')
        assert len(_events(security, 'account_created')) == 1
        assert AccountHistory.objects.filter(user=new_user, action='account_created').exists()


@pytest.mark.django_db
class TestRefusedRequestsNameWhoAndWhere:
    def test_a_forbidden_request_records_the_account_the_address_and_the_url(self, user, security):
        client = APIClient()
        client.force_authenticate(user)

        assert client.get('/api/v1/admin-panel/customers/').status_code == 403

        [line] = _events(security, 'permission_denied')
        assert f'user={user.id}' in line and 'ip=127.0.0.1' in line
        assert 'method=GET' in line and 'path=/api/v1/admin-panel/customers/' in line

    def test_an_unauthenticated_request_is_recorded_with_the_address(self, db, security):
        assert APIClient().get('/api/v1/admin-panel/customers/').status_code in (401, 403)

        [line] = _events(security)
        assert 'ip=127.0.0.1' in line and 'user=none' in line

    def test_a_throttled_request_is_recorded(self, user, security):
        with mock.patch('users.throttles.TESTING', False):
            for _ in range(12):
                _login(password='wrong-password-123')

        assert _events(security, 'throttled')

    def test_a_missing_csrf_token_is_recorded(self, user, security):
        client = APIClient(enforce_csrf_checks=True)

        assert client.post('/api/v1/auth/login/', {'email': EMAIL, 'password': PASSWORD}, format='json').status_code == 403

        assert _events(security, 'csrf_failed')


@pytest.mark.django_db
class TestStaffActionsHaveASourceAddress:
    def test_an_admin_access_log_row_stores_the_client_address(self, db):
        staff = User.objects.create_user(email='staff@example.com', password='x', is_staff=True)
        client = APIClient()
        client.force_authenticate(staff)

        assert client.get('/api/v1/admin-panel/customers/', REMOTE_ADDR='203.0.113.7').status_code == 200

        assert AdminAccessLog.objects.filter(action='customer_list').get().ip_address == '203.0.113.7'


class TestHealthEndpoints:
    def test_liveness_needs_nothing(self, client):
        response = client.get('/healthz/')

        assert (response.status_code, response.json()) == (200, {'status': 'ok'})

    @pytest.mark.django_db
    def test_readiness_checks_the_database_and_the_cache(self, client):
        response = client.get('/readyz/')

        assert (response.status_code, response.json()) == (200, {'status': 'ok'})

    @pytest.mark.django_db
    def test_readiness_fails_with_503_and_no_details_when_the_cache_is_down(self, client):
        with mock.patch('common.health.cache.set', side_effect=ConnectionError('redis down')):
            response = client.get('/readyz/')

        assert response.status_code == 503
        assert response.json() == {'status': 'unavailable'}
