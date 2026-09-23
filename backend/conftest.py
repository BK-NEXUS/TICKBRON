"""
Pytest configuration for TICKBRON backend tests.

This file contains pytest fixtures and configuration for reproducible testing.
"""
import pytest
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set Django settings module for pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


# Test database: pytest-django's built-in django_db_setup creates a separate
# test database and runs migrations. Do not override it with a no-op, or tests
# run against the configured development database instead.


def pytest_sessionstart(session):
    """
    Require PostgreSQL for the test run.

    Production runs on PostgreSQL. SQLite hides real failures (it ignores
    varchar lengths and has no row locks, so the concurrency tests skip).
    Set ALLOW_SQLITE_TESTS=1 to run on SQLite anyway.
    """
    from django.conf import settings

    engine = settings.DATABASES['default']['ENGINE']
    if 'postgresql' not in engine and os.getenv('ALLOW_SQLITE_TESTS') != '1':
        pytest.exit(
            f'Tests must run on PostgreSQL, but DB_ENGINE is {engine!r}. '
            'Configure the DB_* variables in backend/.env, or set ALLOW_SQLITE_TESTS=1 to use SQLite.',
            returncode=4,
        )


@pytest.fixture(autouse=True)
def provider_test_modes(settings):
    """
    Run SMS and payment providers in test mode during tests.

    Both settings default to False outside tests; tests that need the
    production behaviour override them back to False.
    """
    settings.SMS_TEST_MODE = True
    settings.PAYMENT_TEST_MODE = True


@pytest.fixture
def sample_system_settings():
    """
    Provide sample system settings data for testing.
    """
    return {
        'key': 'test_setting',
        'value': 'test_value',
        'description': 'Test setting for unit tests'
    }
