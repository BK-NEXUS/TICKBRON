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


DEFAULT_TEST_RATE_SOURCE = 'test-default'


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'no_default_exchange_rate: the test controls exchange rates itself (no default USD rate)',
    )


@pytest.fixture(autouse=True)
def default_exchange_rate(request, django_db_blocker):
    """
    Give normal database tests an accepted USD rate (R6).

    A USD-priced hotel cannot be booked without a rate (503 exchange_rate_unavailable),
    as in a running system after the first CBU fetch. Tests about rates themselves
    (no rate yet, stale rate, fetch, accept) use the no_default_exchange_rate marker
    and create their own rows. The source is 'test-default', so a rate a test stores
    with make_usd_rate() (source cbu.uz, created later) is the one in use.
    TransactionTestCase tests (not django.test.TestCase) are skipped for the same reason
    as geography_dictionary.
    """
    from django.test import TestCase, TransactionTestCase

    test_instance = getattr(request.node, 'instance', None)
    is_django_testcase = isinstance(test_instance, TestCase)
    if isinstance(test_instance, TransactionTestCase) and not is_django_testcase:
        yield
        return
    if request.node.get_closest_marker('no_default_exchange_rate') is not None:
        yield
        return

    # django.test.TestCase: the row is written inside the class transaction and rolled back with it
    uses_db = (
        is_django_testcase
        or request.node.get_closest_marker('django_db') is not None
        or bool({'db', 'transactional_db'} & set(request.fixturenames))
    )
    if uses_db:
        request.getfixturevalue('django_db_setup')
        if not is_django_testcase:
            # The row must be written inside the test's own transaction (or removed by its flush), never committed
            request.getfixturevalue('transactional_db' if 'transactional_db' in request.fixturenames else 'db')
        with django_db_blocker.unblock():
            from decimal import Decimal

            from currency.cbu import tashkent_today
            from currency.models import ExchangeRate

            ExchangeRate.objects.get_or_create(
                currency='USD', rate_date=tashkent_today(), source=DEFAULT_TEST_RATE_SOURCE, status='accepted',
                defaults={'rate': Decimal('12000.00'), 'nominal': 1},
            )

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
