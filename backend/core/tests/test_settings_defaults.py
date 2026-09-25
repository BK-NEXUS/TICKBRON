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
    'SMS_TEST_MODE', 'PAYMENT_TEST_MODE', 'USE_REDIS_CACHE', 'NUM_PROXIES', 'PYTEST_CURRENT_TEST',
    'SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE',
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


def _load_test_mode_settings(**env_overrides):
    return _load_settings('settings.SMS_TEST_MODE, settings.PAYMENT_TEST_MODE', **env_overrides)


def _cache_backend(**env_overrides):
    return _load_settings("settings.CACHES['default']['BACKEND']", **env_overrides)


PRODUCTION_ENV = {'DEBUG': 'False', 'SECRET_KEY': 'test-secret-key', 'ALLOWED_HOSTS': 'example.com'}


def test_provider_test_modes_default_to_false():
    assert _load_test_mode_settings() == 'False False'


def _env_example_values():
    values = {}
    for line in (BACKEND_DIR / '.env.example').read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            values[key.strip()] = value.split('#', 1)[0].strip()
    return values


def test_env_example_keeps_provider_test_modes_off():
    # Copying .env.example must not turn on OTP codes in responses or client-side payment confirmation
    values = _env_example_values()
    assert values.get('SMS_TEST_MODE', 'False').lower() == 'false'
    assert values.get('PAYMENT_TEST_MODE', 'False').lower() == 'false'


def test_provider_test_modes_can_be_enabled_explicitly():
    assert _load_test_mode_settings(SMS_TEST_MODE='True', PAYMENT_TEST_MODE='True') == 'True True'


def test_production_uses_redis_cache_by_default():
    assert _cache_backend(**PRODUCTION_ENV) == 'django_redis.cache.RedisCache'


def test_debug_uses_local_memory_cache_by_default():
    assert _cache_backend(DEBUG='True') == 'django.core.cache.backends.locmem.LocMemCache'


def test_cache_backend_can_be_chosen_explicitly():
    assert _cache_backend(DEBUG='True', USE_REDIS_CACHE='True') == 'django_redis.cache.RedisCache'
    assert _cache_backend(USE_REDIS_CACHE='False', **PRODUCTION_ENV) == \
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
    assert _secure_cookies(SESSION_COOKIE_SECURE='False', CSRF_COOKIE_SECURE='False', **PRODUCTION_ENV) == \
        'False False'
    assert _secure_cookies(DEBUG='True', SESSION_COOKIE_SECURE='True', CSRF_COOKIE_SECURE='True') == \
        'True True'
