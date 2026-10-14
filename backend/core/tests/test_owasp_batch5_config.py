"""
A02 (OWASP 2025) configuration gaps found by the audit.

- DEBUG=True with a real domain was never checked (the start-up guard only ran with DEBUG off)
- production could boot on the SQLite default when DB_* were forgotten (no row locks: double bookings)
- the DRF browsable API stayed on in production
- ALLOWED_HOSTS="a.com, b.com" silently lost the second host
- no health check on persistent DB connections, no timeouts on the cache
- one huge JSON body was buffered by a worker
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.test import Client

from core.tests.test_r4_production_config import EXTRA_ISOLATED, GOOD_PRODUCTION_ENV
from core.tests.test_settings_defaults import BACKEND_DIR, ISOLATED_ENV_VARS, LOAD_SETTINGS


def _run(expression, **overrides):
    env = {k: v for k, v in os.environ.items() if k not in ISOLATED_ENV_VARS + EXTRA_ISOLATED}
    env.update({'DJANGO_SETTINGS_MODULE': 'config.settings'})
    env.update(GOOD_PRODUCTION_ENV)
    env.update(overrides)
    env = {k: v for k, v in env.items() if v is not None}
    return subprocess.run(
        [sys.executable, '-c', LOAD_SETTINGS.format(expression=expression)],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120,
    )


def _value(expression, **overrides):
    result = _run(expression, **overrides)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip().splitlines()[-1]


class TestDebugGuard:
    def test_debug_with_a_real_domain_refuses_to_start(self):
        result = _run('1', DEBUG='True', ALLOWED_HOSTS='tickbron.uz')

        assert result.returncode != 0
        assert 'DEBUG' in result.stderr

    @pytest.mark.parametrize('hosts', ['localhost', 'localhost,127.0.0.1,[::1]', 'localhost,192.168.1.5', None])
    def test_debug_on_localhost_and_ip_addresses_still_starts(self, hosts):
        result = _run('1', DEBUG='True', ALLOWED_HOSTS=hosts, SECRET_KEY=None)

        assert result.returncode == 0, result.stderr

    def test_production_needs_postgresql(self):
        result = _run('1', DB_ENGINE='django.db.backends.sqlite3')

        assert result.returncode != 0
        assert 'DB_ENGINE' in result.stderr

    def test_example_env_does_not_ship_debug_on(self):
        lines = (Path(BACKEND_DIR) / '.env.example').read_text().splitlines()

        assert 'DEBUG=False' in lines
        assert 'DEBUG=True' not in lines


class TestSettingsValues:
    def test_only_json_is_rendered_in_production(self):
        renderers = _value("settings.REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES']")

        assert renderers == "['rest_framework.renderers.JSONRenderer']"

    def test_the_browsable_api_stays_available_in_local_development(self):
        renderers = _value("settings.REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES']", DEBUG='True', SECRET_KEY=None, ALLOWED_HOSTS=None)

        assert 'BrowsableAPIRenderer' in renderers

    def test_environment_lists_are_stripped(self):
        hosts = _value('settings.ALLOWED_HOSTS', DEBUG='True', ALLOWED_HOSTS='localhost, 127.0.0.1 ,')

        assert hosts == "['localhost', '127.0.0.1']"

    def test_persistent_connections_are_health_checked(self):
        assert _value("settings.DATABASES['default']['CONN_HEALTH_CHECKS']") == 'True'

    def test_the_unused_health_check_settings_are_gone(self):
        assert _value("hasattr(settings, 'DATABASE_HEALTH_CHECK_ENABLED')") == 'False'

    def test_the_cache_has_socket_timeouts(self):
        options = _value("settings.CACHES['default']['OPTIONS']", USE_REDIS_CACHE='True')

        assert "'SOCKET_CONNECT_TIMEOUT': 2" in options
        assert "'SOCKET_TIMEOUT': 2" in options


class TestRequestSizeAndHeaders:
    def test_a_huge_json_body_is_refused_before_it_is_read(self):
        response = Client().post('/api/v1/auth/login/', '{}', content_type='application/json',
                                 CONTENT_LENGTH=str(5 * 1024 * 1024))

        assert response.status_code == 413

    def test_a_normal_json_body_still_passes(self):
        response = Client().post('/api/v1/auth/login/', '{"email": "a@b.uz", "password": "x"}',
                                 content_type='application/json')

        assert response.status_code != 413

    def test_the_legacy_xss_header_is_switched_off(self):
        assert Client().get('/api/v1/properties/filter-options/')['X-XSS-Protection'] == '0'
