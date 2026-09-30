"""
Pytest configuration for TICKBRON backend tests.

This file contains pytest fixtures and configuration for reproducible testing.
"""
import os
import sys
from pathlib import Path

import pytest


# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set Django settings module for pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Shared data for the Status endpoint tests (admin_panel and partner)
pytest_plugins = ['admin_panel.tests.status_fixtures']


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
            f"Tests must run on PostgreSQL, but DB_ENGINE is {engine!r}. "
            'Configure the DB_* variables in backend/.env, or set '
            'ALLOW_SQLITE_TESTS=1 to use SQLite anyway.',
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


@pytest.fixture(autouse=True)
def geography_dictionary(request, django_db_blocker):
    """
    Keep the Geography dictionary available for normal database tests.

    Geography data is loaded by the geography data migration. Some
    TransactionTestCase-based migration tests intentionally manipulate
    database state and use serialized rollback. Injecting Geography data
    into those tests can conflict with Django's serialized database restore.

    Therefore this fixture only reloads Geography data for normal database
    tests and explicitly skips TransactionTestCase-based tests.
    """
    from django.test import TransactionTestCase

    test_instance = getattr(request.node, 'instance', None)

    # Migration/TransactionTestCase tests must control their own database
    # state. Do not inject Geography rows into their serialized rollback.
    if isinstance(test_instance, TransactionTestCase):
        yield
        return

    uses_db = (
        request.node.get_closest_marker('django_db') is not None
        or bool({'db', 'transactional_db'} & set(request.fixturenames))
    )

    if uses_db:
        # Ensure the test database exists before accessing Geography.
        request.getfixturevalue('django_db_setup')

        with django_db_blocker.unblock():
            from geography.data import load_geography
            from geography.models import City, Country, Region

            # A previous TransactionTestCase can empty the dictionary.
            # Reload it only when it is genuinely empty.
            if not Country.objects.exists():
                load_geography(Country, Region, City)

    yield


@pytest.fixture(autouse=True)
def clear_cache():
    """Start every test with an empty cache."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def sample_system_settings():
    """
    Provide sample system settings data for testing.
    """
    return {
        'key': 'test_setting',
        'value': 'test_value',
        'description': 'Test system setting',
    }