"""
backend/.env.dev.example is the ready-to-copy file for a developer's own machine (also when shared through ngrok):
nothing in it is commented out, it reads only variables the settings know, and it can never be mistaken for a
server file (DEBUG on, a dev-only secret, no real password).
"""
from pathlib import Path

from core.tests.test_env_example_complete import BACKEND_DIR, _variables_read

DEV_EXAMPLE = Path(BACKEND_DIR) / '.env.dev.example'


def _values():
    values = {}
    for line in DEV_EXAMPLE.read_text(encoding='utf-8').splitlines():
        if line.strip() and not line.lstrip().startswith('#'):
            name, _, value = line.partition('=')
            values[name.strip()] = value.strip()
    return values


def test_it_sets_only_variables_the_settings_read():
    assert not sorted(set(_values()) - _variables_read())


def test_no_setting_is_left_commented_out():
    commented = [line for line in DEV_EXAMPLE.read_text(encoding='utf-8').splitlines()
                 if line.startswith('#') and '=' in line and line[1:].strip().split('=')[0].isupper()]
    assert not commented, commented


def test_it_is_for_development_only():
    values = _values()
    assert values['DEBUG'] == 'True'
    assert 'dev-only' in values['SECRET_KEY']
    assert '*' not in values['ALLOWED_HOSTS']
    assert values['EMAIL_HOST'] == ''
    assert values['TELEGRAM_BOT_TOKEN'] == ''


def test_the_tunnel_address_is_trusted_for_forms():
    assert 'ngrok' in _values()['CSRF_TRUSTED_ORIGINS']


def test_background_tasks_run_without_a_worker():
    assert _values()['CELERY_TASK_ALWAYS_EAGER'] == 'True'
