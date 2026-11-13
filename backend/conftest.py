"""
TICKBRON backend testleri ushın pytest konfiguraciyası.

Bul fayl qaytalanatuǵın testlew ushın pytest fixture lerin hám konfiguraciyanı óz ishine aladı.
"""
import os
import sys
from pathlib import Path

import pytest


# Backend papkasın Python jolına qosıw
sys.path.insert(0, str(Path(__file__).parent))

# pytest ushın Django sazlama modulin belgilew
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Status endpoint testleri ushın ortaq maǵlıwmat (admin_panel hám partner)
pytest_plugins = ['admin_panel.tests.status_fixtures']


# Test database: pytest-django tiń ishki django_db_setup ı bólek test database
# jaratadı hám migration lardı isletedi. Onı bosı menen almastırmań, bolmasa testler
# sazlanǵan development database ge qarsı isleydi.


@pytest.fixture(autouse=True)
def geography_dictionary(request, django_db_blocker):
    """
    Geografiya sózligin ádettegi database testleri ushın bar etip saqlaw.

    Geografiya maǵlıwmatı geografiya data migration ı tárepinen júklenedi. Ayırım
    TransactionTestCase tiykarındaǵı migration testleri ataylap database jaǵdayın ózgertedi
    hám serialized rollback paydalanadı. Geografiya maǵlıwmatın olarǵa kirgiziw
    Django nıń serialized database tikleniwi menen qaqtıǵıwı múmkin.

    Sol sebepli bul fixture Geografiya maǵlıwmatın tek ádettegi database
    testleri ushın qayta júkleydi hám TransactionTestCase tiykarındaǵı testlerdi anıq ótkizip jiberedi.
    """
    from django.test import TransactionTestCase

    test_instance = getattr(request.node, 'instance', None)

    # Migration/TransactionTestCase testleri óz database jaǵdayın ózleri basqarıwı kerek.
    # Geografiya qatarların olardıń serialized rollback ına kirgizbeń.
    if isinstance(test_instance, TransactionTestCase):
        yield
        return

    uses_db = (
        request.node.get_closest_marker('django_db') is not None
        or bool({'db', 'transactional_db'} & set(request.fixturenames))
    )

    if uses_db:
        # Geografiyaǵa kiriwden aldın test database bar ekenin támiyinlew.
        request.getfixturevalue('django_db_setup')

        with django_db_blocker.unblock():
            from geography.data import load_geography
            from geography.models import Country, Region

            # Aldınǵı TransactionTestCase sózlikti bosatıp jiberiwi múmkin.
            # Tek haqıyqatında bos bolǵanda qayta júkleń.
            if not Country.objects.exists():
                load_geography(Country, Region)

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
    Ádettegi database testlerine qabıllanǵan USD kursın beriw (R6).

    USD de bahalanǵan mehmanxananı kurssız bronlap bolmaydı (503 exchange_rate_unavailable),
    birinshi CBU alıwdan keyin isleytuǵın sistemadaǵıday. Kurslardıń ózi haqqındaǵı testler
    (kurs ele joq, eskirgen kurs, alıw, qabıllaw) no_default_exchange_rate belgisin paydalanadı
    hám óz qatarların jaratadı. Dereg 'test-default', sol sebepli testtiń make_usd_rate() penen saqlaǵan kursı
    (cbu.uz dereg i, keyin jaratılǵan) paydalanılatuǵını.
    TransactionTestCase testleri (django.test.TestCase emes) geography_dictionary menen birdey sebepten ótkizip
    jiberiledi.
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

    # django.test.TestCase: qatar klas transaction ı ishinde jazıladı hám onıń menen qaytadı
    uses_db = (
        is_django_testcase
        or request.node.get_closest_marker('django_db') is not None
        or bool({'db', 'transactional_db'} & set(request.fixturenames))
    )
    if uses_db:
        request.getfixturevalue('django_db_setup')
        if not is_django_testcase:
            # Qatar testtiń óz transaction ı ishinde jazılıwı kerek (yamasa flush penen alıp taslanadı), hesh qashan commit
            # qılınbaydı
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
def mailed_codes_off_by_default(settings):
    """
    E-mail ge jiberiletuǵın altı sanlı kodlar isleytuǵın sistemada qosılǵan, biraq kópshilik testler adamlardı API arqalı
    tek
    parol menen dizimnen ótkizedi hám kirgizedi: olar kodlarsız isleydi. Kodlardıń ózi haqqındaǵı testler
    (users/tests/test_email_codes.py)
    olardı qosadı.
    """
    settings.EMAIL_VERIFICATION_REQUIRED = False
    settings.EMAIL_LOGIN_CODE_REQUIRED = False


@pytest.fixture(autouse=True)
def clear_cache():
    """Hár testti bos kesh penen baslaw."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def sample_system_settings():
    """
    Testlew ushın úlgi sistema sazlamaları maǵlıwmatın beriw.
    """
    return {
        'key': 'test_setting',
        'value': 'test_value',
        'description': 'Test system setting',
    }
