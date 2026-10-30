"""
R4 security review: with DEBUG off the app refuses to start on insecure settings.

Before, only an unset SECRET_KEY / ALLOWED_HOSTS stopped startup. The .env.example
placeholder key was accepted, and CORS / CSRF origins silently fell back to
http://localhost:3000.
"""
import os
import subprocess
import sys

import pytest

from core.tests.test_settings_defaults import BACKEND_DIR, ISOLATED_ENV_VARS, LOAD_SETTINGS

FERNET_KEY = 'D7eMmWkvKa9v2OeQIO0bLAKuod5UPZ9jR1n2vge7atk='
STRONG_KEY = 'k' * 20 + '-Production-Secret-Key-For-Tests-0123456789'
GOOD_PRODUCTION_ENV = {
    'DEBUG': 'False',
    'SECRET_KEY': STRONG_KEY,
    'ALLOWED_HOSTS': 'tickbron.uz',
    'CORS_ALLOWED_ORIGINS': 'https://tickbron.uz',
    'CSRF_TRUSTED_ORIGINS': 'https://tickbron.uz',
    # N-3/N-6: behind one TLS-terminating proxy (nginx)
    'NUM_PROXIES': '1',
    'USE_X_FORWARDED_PROTO': 'True',
    'SECURE_SSL_REDIRECT': 'True',
    'FRONTEND_URL': 'https://tickbron.uz', 'EMAIL_HOST': 'smtp.tickbron.uz',  # password reset links and mail
    'TWO_FACTOR_REQUIRED_FOR_ADMINS': 'True', 'TWO_FACTOR_KEY': FERNET_KEY,  # then the sealing key is required
}
EXTRA_ISOLATED = ('SECRET_KEY', 'ALLOWED_HOSTS', 'CORS_ALLOWED_ORIGINS', 'CSRF_TRUSTED_ORIGINS')

# `manage.py check --deploy` with .env loading off, so a developer's .env cannot change the result
CHECK_DEPLOY = (
    "import dotenv; dotenv.load_dotenv = lambda *a, **k: None\n"
    "from django.core.management import execute_from_command_line\n"
    "execute_from_command_line(['manage.py', 'check', '--deploy', '--fail-level', 'WARNING'])\n"
)


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
    ({'SECRET_KEY': 'your-secret-key-here-change-in-production'}, 'SECRET_KEY'),
    ({'SECRET_KEY': 'django-insecure-' + 'x' * 50}, 'SECRET_KEY'),
    ({'SECRET_KEY': 'short-key'}, 'SECRET_KEY'),
    ({'ALLOWED_HOSTS': '*'}, 'ALLOWED_HOSTS'),
    ({'CORS_ALLOWED_ORIGINS': None}, 'CORS_ALLOWED_ORIGINS'),
    ({'CSRF_TRUSTED_ORIGINS': None}, 'CSRF_TRUSTED_ORIGINS'),
    ({'CORS_ALLOWED_ORIGINS': 'http://tickbron.uz'}, 'CORS_ALLOWED_ORIGINS'),
    ({'CSRF_TRUSTED_ORIGINS': 'https://tickbron.uz,http://localhost:3000'}, 'CSRF_TRUSTED_ORIGINS'),
    # N-3: an unset proxy count would put every visitor in one throttle/lockout bucket
    ({'NUM_PROXIES': None}, 'NUM_PROXIES'),
    ({'NUM_PROXIES': '-1'}, 'NUM_PROXIES'),
    ({'NUM_PROXIES': 'two'}, 'NUM_PROXIES'),
    # N-6: https must be enforced, and the proxy header trusted when a proxy terminates TLS
    ({'SECURE_SSL_REDIRECT': 'False'}, 'SECURE_SSL_REDIRECT'),
    ({'USE_X_FORWARDED_PROTO': 'False'}, 'USE_X_FORWARDED_PROTO'),
    # N-19
    ({'SESSION_COOKIE_SECURE': 'False'}, 'SESSION_COOKIE_SECURE'),
    ({'CSRF_COOKIE_SECURE': 'False'}, 'CSRF_COOKIE_SECURE'),
    ({'USE_REDIS_CACHE': 'False'}, 'USE_REDIS_CACHE'),
    ({'DB_HOST': 'db.example.com', 'DB_SSLMODE': 'prefer'}, 'DB_SSLMODE'),
    ({'TWO_FACTOR_KEY': None}, 'TWO_FACTOR_KEY'),
    ({'TWO_FACTOR_KEY': 'not-a-key'}, 'TWO_FACTOR_KEY'),
])
def test_insecure_production_settings_refuse_to_start(overrides, message):
    result = _start(**overrides)

    assert result.returncode != 0
    assert message in result.stderr


def test_no_proxy_deployment_may_skip_the_forwarded_proto_header():
    result = _start(NUM_PROXIES='0', USE_X_FORWARDED_PROTO='False')
    assert result.returncode == 0, result.stderr


def test_remote_database_with_required_tls_starts():
    result = _start(DB_HOST='db.example.com', DB_SSLMODE='require')
    assert result.returncode == 0, result.stderr


def test_docker_database_container_on_the_private_network_starts_without_tls():
    # docker-compose.yml: the database is the container called `db`, reached over Docker's own network
    result = _start(DB_HOST='db', DB_SSLMODE='prefer', DB_NETWORK_IS_PRIVATE='True')
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('host', ['db.example.com', '10.0.0.5', 'db.internal'])
def test_the_private_network_declaration_does_not_cover_a_real_address(host):
    # a dotted name or an IP address is never a Docker service name: TLS stays required
    result = _start(DB_HOST=host, DB_SSLMODE='prefer', DB_NETWORK_IS_PRIVATE='True')
    assert result.returncode != 0
    assert 'DB_SSLMODE' in result.stderr


def test_a_service_name_without_the_declaration_still_needs_tls():
    result = _start(DB_HOST='db', DB_SSLMODE='prefer')
    assert result.returncode != 0
    assert 'DB_SSLMODE' in result.stderr


def test_debug_still_allows_local_development_values():
    result = _start(
        DEBUG='True', SECRET_KEY=None, ALLOWED_HOSTS=None, CORS_ALLOWED_ORIGINS=None,
        CSRF_TRUSTED_ORIGINS=None,
    )
    assert result.returncode == 0, result.stderr


def test_check_deploy_reports_no_issues():
    env = {k: v for k, v in os.environ.items() if k not in ISOLATED_ENV_VARS + EXTRA_ISOLATED}
    env.update(GOOD_PRODUCTION_ENV, DJANGO_SETTINGS_MODULE='config.settings')
    result = subprocess.run(
        [sys.executable, '-c', CHECK_DEPLOY],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'no issues' in result.stdout


def test_without_the_two_factor_requirement_the_key_is_not_needed():
    result = _start(TWO_FACTOR_REQUIRED_FOR_ADMINS='False', TWO_FACTOR_KEY=None)
    assert result.returncode == 0, result.stderr


def _requirement(**overrides):
    env = {k: v for k, v in os.environ.items() if k not in ISOLATED_ENV_VARS + EXTRA_ISOLATED}
    env.update({'DJANGO_SETTINGS_MODULE': 'config.settings', **GOOD_PRODUCTION_ENV, **overrides})
    if 'TWO_FACTOR_REQUIRED_FOR_ADMINS' not in overrides:
        env.pop('TWO_FACTOR_REQUIRED_FOR_ADMINS')  # what the code decides when nobody set it
    env = {k: v for k, v in env.items() if v is not None}
    result = subprocess.run(
        [sys.executable, '-c', LOAD_SETTINGS.format(expression='settings.TWO_FACTOR_REQUIRED_FOR_ADMINS')],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip().splitlines()[-1]


def test_two_step_sign_in_is_required_for_administrators_in_production_by_default():
    assert _requirement() == 'True'


def test_two_step_sign_in_is_off_by_default_for_local_development():
    assert _requirement(DEBUG='True', ALLOWED_HOSTS='localhost') == 'False'


def test_the_refusal_tells_a_developer_how_to_get_past_it():
    result = _start(SECRET_KEY='short-key')

    assert result.returncode != 0
    assert 'set DEBUG=True in backend/.env' in result.stderr
