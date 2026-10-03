"""
R4 security review: with DEBUG off the app refuses to start on insecure settings.

Before, only an unset SECRET_KEY / ALLOWED_HOSTS stopped startup. SMS_TEST_MODE=True
with DEBUG=False returned every OTP code in the /auth/otp/request/ response (anyone
could log in as any phone number), the .env.example placeholder key was accepted,
and CORS / CSRF origins silently fell back to http://localhost:3000.
"""
import os
import subprocess
import sys

import pytest

from core.tests.test_settings_defaults import BACKEND_DIR, ISOLATED_ENV_VARS, LOAD_SETTINGS

STRONG_KEY = 'k' * 20 + '-Production-Secret-Key-For-Tests-0123456789'
GOOD_PRODUCTION_ENV = {
    'DEBUG': 'False',
    'SECRET_KEY': STRONG_KEY,
    'ALLOWED_HOSTS': 'tickbron.uz',
    'CORS_ALLOWED_ORIGINS': 'https://tickbron.uz',
    'CSRF_TRUSTED_ORIGINS': 'https://tickbron.uz',
}
EXTRA_ISOLATED = ('SECRET_KEY', 'ALLOWED_HOSTS', 'CORS_ALLOWED_ORIGINS', 'CSRF_TRUSTED_ORIGINS')


def _start(**env_overrides):
    env = {k: v for k, v in os.environ.items() if k not in ISOLATED_ENV_VARS + EXTRA_ISOLATED}
    env.update({'DJANGO_SETTINGS_MODULE': 'config.settings'})
    env.update(GOOD_PRODUCTION_ENV)
    env.update(env_overrides)
    env = {k: v for k, v in env.items() if v is not None}
    return subprocess.run(
        [sys.executable, '-c', LOAD_SETTINGS.format(expression='settings.DEBUG')],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120,
    )


def test_good_production_settings_start():
    result = _start()
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('overrides, message', [
    ({'SMS_TEST_MODE': 'True'}, 'SMS_TEST_MODE'),
    ({'PAYMENT_TEST_MODE': 'True'}, 'PAYMENT_TEST_MODE'),
    ({'SECRET_KEY': 'your-secret-key-here-change-in-production'}, 'SECRET_KEY'),
    ({'SECRET_KEY': 'django-insecure-' + 'x' * 50}, 'SECRET_KEY'),
    ({'SECRET_KEY': 'short-key'}, 'SECRET_KEY'),
    ({'ALLOWED_HOSTS': '*'}, 'ALLOWED_HOSTS'),
    ({'CORS_ALLOWED_ORIGINS': None}, 'CORS_ALLOWED_ORIGINS'),
    ({'CSRF_TRUSTED_ORIGINS': None}, 'CSRF_TRUSTED_ORIGINS'),
    ({'CORS_ALLOWED_ORIGINS': 'http://tickbron.uz'}, 'CORS_ALLOWED_ORIGINS'),
    ({'CSRF_TRUSTED_ORIGINS': 'https://tickbron.uz,http://localhost:3000'}, 'CSRF_TRUSTED_ORIGINS'),
])
def test_insecure_production_settings_refuse_to_start(overrides, message):
    result = _start(**overrides)

    assert result.returncode != 0
    assert message in result.stderr


def test_debug_still_allows_local_development_values():
    result = _start(
        DEBUG='True', SECRET_KEY=None, ALLOWED_HOSTS=None, CORS_ALLOWED_ORIGINS=None,
        CSRF_TRUSTED_ORIGINS=None, SMS_TEST_MODE='True', PAYMENT_TEST_MODE='True',
    )
    assert result.returncode == 0, result.stderr
