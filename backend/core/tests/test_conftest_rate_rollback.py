"""
The default USD rate (conftest.default_exchange_rate) must live inside the test's own transaction.
Written outside it, a test that gets the database only through a fixture would leave a committed rate row
behind and break the exchange-rate tests that run later.
"""
import pytest

from conftest import DEFAULT_TEST_RATE_SOURCE
from currency.models import ExchangeRate


@pytest.fixture
def needs_the_database(db):
    return None


def test_the_default_rate_is_written_inside_the_tests_transaction(needs_the_database):
    from django.db import connection

    assert connection.in_atomic_block
    assert ExchangeRate.objects.filter(source=DEFAULT_TEST_RATE_SOURCE).exists()


def test_the_previous_test_left_no_rate_behind(django_db_blocker):
    with django_db_blocker.unblock():
        assert not ExchangeRate.objects.filter(source=DEFAULT_TEST_RATE_SOURCE).exists()
