"""
Tests for security-sensitive settings defaults.
"""
import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]

# Load settings in a clean interpreter with .env loading disabled, so the
# values reflect the code defaults rather than the developer's .env file.
LOAD_SETTINGS = (
    "import dotenv; dotenv.load_dotenv = lambda *a, **k: None\n"
    "import django; django.setup()\n"
    "from django.conf import settings\n"
    "print(settings.SMS_TEST_MODE, settings.PAYMENT_TEST_MODE)\n"
)


def _load_test_mode_settings(**env_overrides):
    env = {k: v for k, v in os.environ.items()
           if k not in ('SMS_TEST_MODE', 'PAYMENT_TEST_MODE')}
    env.update({'DJANGO_SETTINGS_MODULE': 'config.settings', 'DEBUG': 'True'})
    env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, '-c', LOAD_SETTINGS],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip().splitlines()[-1]


def test_provider_test_modes_default_to_false():
    assert _load_test_mode_settings() == 'False False'


def test_provider_test_modes_can_be_enabled_explicitly():
    assert _load_test_mode_settings(SMS_TEST_MODE='True', PAYMENT_TEST_MODE='True') == 'True True'
