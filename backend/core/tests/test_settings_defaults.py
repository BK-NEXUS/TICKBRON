"""
Tests for security-sensitive settings defaults.
"""
import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]

# Variables that must come from each test, not from the developer's shell or
# from pytest itself (PYTEST_CURRENT_TEST makes settings think it is a test run)
ISOLATED_ENV_VARS = (
    'USE_REDIS_CACHE', 'NUM_PROXIES', 'PYTEST_CURRENT_TEST',
    'SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE', 'THROTTLE_ANON_RATE', 'THROTTLE_USER_RATE',
    'USE_X_FORWARDED_PROTO', 'SECURE_SSL_REDIRECT', 'SECURE_HSTS_PRELOAD', 'SESSION_COOKIE_AGE',
    'DB_HOST', 'DB_SSLMODE', 'DB_NETWORK_IS_PRIVATE', 'FRONTEND_URL', 'EMAIL_HOST', 'EMAIL_BACKEND',
    'TWO_FACTOR_REQUIRED_FOR_ADMINS', 'TWO_FACTOR_KEY',
)

# Load settings in a clean interpreter with .env loading disabled, so the
# values reflect the code defaults rather than the developer's .env file.
LOAD_SETTINGS = (
    "import dotenv; dotenv.load_dotenv = lambda *a, **k: None\n"
    "import django; django.setup()\n"
    "from django.conf import settings\n"
    "print({expression})\n"
)


def _load_settings(expression, **env_overrides):
    env = {k: v for k, v in os.environ.items() if k not in ISOLATED_ENV_VARS}
    env.update({'DJANGO_SETTINGS_MODULE': 'config.settings', 'DEBUG': 'True'})
    env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, '-c', LOAD_SETTINGS.format(expression=expression)],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip().splitlines()[-1]


def _cache_backend(**env_overrides):
    return _load_settings("settings.CACHES['default']['BACKEND']", **env_overrides)


# Must pass the production startup checks (core/tests/test_r4_production_config.py)
PRODUCTION_ENV = {
    'DEBUG': 'False', 'SECRET_KEY': 'test-secret-key-' + 'x' * 40, 'ALLOWED_HOSTS': 'example.com',
    'CORS_ALLOWED_ORIGINS': 'https://example.com', 'CSRF_TRUSTED_ORIGINS': 'https://example.com',
    'NUM_PROXIES': '1', 'USE_X_FORWARDED_PROTO': 'True', 'SECURE_SSL_REDIRECT': 'True',
    'FRONTEND_URL': 'https://example.com', 'EMAIL_HOST': 'smtp.example.com',  # password reset links and mail
    'TWO_FACTOR_REQUIRED_FOR_ADMINS': 'True', 'TWO_FACTOR_KEY': 'D7eMmWkvKa9v2OeQIO0bLAKuod5UPZ9jR1n2vge7atk=',
}


def test_production_uses_redis_cache_by_default():
    assert _cache_backend(**PRODUCTION_ENV) == 'django_redis.cache.RedisCache'


def test_debug_uses_local_memory_cache_by_default():
    assert _cache_backend(DEBUG='True') == 'django.core.cache.backends.locmem.LocMemCache'


def test_cache_backend_can_be_chosen_explicitly():
    assert _cache_backend(DEBUG='True', USE_REDIS_CACHE='True') == 'django_redis.cache.RedisCache'
    # N-19: production refuses USE_REDIS_CACHE=False (see test_r4_production_config), so the switch is local-only
    assert _cache_backend(DEBUG='True', USE_REDIS_CACHE='False') == \
        'django.core.cache.backends.locmem.LocMemCache'


def test_forwarded_for_is_ignored_by_default():
    assert _load_settings("settings.NUM_PROXIES, settings.REST_FRAMEWORK['NUM_PROXIES']") == '0 0'


def _secure_cookies(**env_overrides):
    return _load_settings('settings.SESSION_COOKIE_SECURE, settings.CSRF_COOKIE_SECURE', **env_overrides)


def test_production_cookies_are_secure_by_default():
    assert _secure_cookies(**PRODUCTION_ENV) == 'True True'


def test_debug_cookies_are_not_secure_by_default():
    # Local development runs over plain http
    assert _secure_cookies(DEBUG='True') == 'False False'


def test_cookie_security_can_be_set_explicitly():
    # N-19: production refuses insecure cookies (see test_r4_production_config), so only DEBUG may turn them off
    assert _secure_cookies(DEBUG='True', SESSION_COOKIE_SECURE='False', CSRF_COOKIE_SECURE='False') == \
        'False False'
    assert _secure_cookies(DEBUG='True', SESSION_COOKIE_SECURE='True', CSRF_COOKIE_SECURE='True') == \
        'True True'


def _throttle_rates(**env_overrides):
    return _load_settings("settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']", **env_overrides)


def test_anonymous_browsing_limit_allows_normal_use():
    # One property page makes ~6 anonymous requests; 100/hour blocked visitors after ~15 pages (E2E BUG 7)
    # R12b: the no_show_report scope joined the throttle rates; anon and user are unchanged
    # N-7: the booking_create scope joined the rates; anon and user are still unchanged
    # The support chat added the chat_send and chat_poll scopes; the others are unchanged
    assert _throttle_rates() == (
        "{'anon': '2000/hour', 'user': '1000/hour', 'booking_create': '30/hour', "
        "'no_show_report': '20/hour', 'chat_send': '20/min', 'chat_poll': '90/min'}"
    )


def test_anonymous_limit_can_be_set_from_the_environment():
    assert "'anon': '300/hour'" in _throttle_rates(THROTTLE_ANON_RATE='300/hour')


def test_user_limit_can_be_set_from_the_environment():
    # The E2E crawl loads every page as the demo accounts many times
    assert "'user': '100000/hour'" in _throttle_rates(THROTTLE_USER_RATE='100000/hour')


def test_sensitive_endpoints_keep_their_strict_limits():
    from users.throttles import (
        LoginRateThrottle, RegisterRateThrottle,
    )

    assert LoginRateThrottle.rate == '10/min'
    assert RegisterRateThrottle.rate == '5/min'


def _test_db_name(**env_overrides):
    env = {'DB_NAME': 'tickbron', **env_overrides}
    return _load_settings("settings.DATABASES['default'].get('TEST', {}).get('NAME')", **env)


def test_test_database_name_is_djangos_default_without_a_suffix():
    assert _test_db_name(TICKBRON_TEST_DB_SUFFIX='') == 'None'


def test_test_database_suffix_gives_each_session_its_own_database():
    assert _test_db_name(TICKBRON_TEST_DB_SUFFIX='r12') == 'test_tickbron_r12'


def test_test_database_suffix_refuses_unsafe_characters():
    env = {k: v for k, v in os.environ.items() if k not in ISOLATED_ENV_VARS}
    env.update({'DJANGO_SETTINGS_MODULE': 'config.settings', 'DEBUG': 'True', 'TICKBRON_TEST_DB_SUFFIX': 'a;b'})
    result = subprocess.run(
        [sys.executable, '-c', LOAD_SETTINGS.format(expression='1')],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode != 0
    assert 'TICKBRON_TEST_DB_SUFFIX' in result.stderr


def test_hsts_preload_is_off_by_default():
    # Preload is hard to undo, so the owner opts in explicitly (N-6)
    assert _load_settings('settings.SECURE_HSTS_PRELOAD') == 'False'
    assert _load_settings('settings.SECURE_HSTS_PRELOAD', SECURE_HSTS_PRELOAD='True') == 'True'


def test_proxy_ssl_header_is_only_trusted_when_asked():
    assert _load_settings('settings.SECURE_PROXY_SSL_HEADER') == 'None'
    assert _load_settings('settings.SECURE_PROXY_SSL_HEADER', USE_X_FORWARDED_PROTO='True') == \
        "('HTTP_X_FORWARDED_PROTO', 'https')"


def test_sessions_last_a_week_by_default():
    assert _load_settings('settings.SESSION_COOKIE_AGE') == str(7 * 24 * 3600)
    assert _load_settings('settings.SESSION_COOKIE_AGE', SESSION_COOKIE_AGE='3600') == '3600'
