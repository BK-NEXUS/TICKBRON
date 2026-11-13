"""
Ádetdegi USD kursı (conftest.default_exchange_rate) testtiń óz transaction ı ishinde bolıwı kerek.
Onnan sırtında jazılsa, database di tek fixture arqalı alatuǵın test commit qılınǵan kurs qatarın
qaldırıp, keyin isleytuǵın valyuta kursı testlerin buzar edi.
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
