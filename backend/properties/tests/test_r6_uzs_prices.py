"""
R6 decision D: search results and property pages show an informational price in so'm
(`base_price_uzs_approx`, the name says it is approximate) next to the base price. One
rate lookup per request, never one per property. What a guest pays always comes from
the booking snapshot, not from this field.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from currency.cbu import tashkent_today
from currency.models import ExchangeRate
from properties.models import Property, PropertyType
from users.models import User


def _hotel(owner, kind, name, price, currency):
    return Property.objects.create(
        owner=owner, property_type=kind, status='active', max_guests=2, bedrooms=1, bathrooms=1,
        address_line1='1 Main', city='Tashkent', country='Uzbekistan', base_price=price, currency=currency,
    )


@pytest.fixture
def hotels(db):
    owner = User.objects.create_user(email='owner-r6@example.com', password='OwnerPassword#123')
    kind = PropertyType.objects.create(name='Hotel', slug='hotel')
    return {
        'usd': [_hotel(owner, kind, f'USD {i}', Decimal('100.00') + i, 'USD') for i in range(3)],
        'uzs': _hotel(owner, kind, 'UZS', Decimal('650000'), 'UZS'),
    }


def _rate(rate='11772.95', days_old=0):
    ExchangeRate.objects.create(currency='USD', rate=Decimal(rate), nominal=1, source='cbu.uz', status='accepted',
                                rate_date=tashkent_today() - timedelta(days=days_old))


def _search():
    response = APIClient().get('/api/v1/properties/search/')
    assert response.status_code == 200
    return {row['id']: row for row in response.data['results']}


@pytest.mark.django_db
class TestSearch:

    def test_usd_and_uzs_hotels_carry_an_approximate_uzs_price(self, hotels):
        _rate()
        rows = _search()

        usd = rows[hotels['usd'][0].id]
        assert (usd['base_price'], usd['currency']) == ('100.00', 'USD')
        assert usd['base_price_uzs_approx'] == '1177295.00'
        assert usd['uzs_rate'] == {'rate': '11772.950000', 'date': tashkent_today().isoformat(),
                                   'source': 'cbu.uz', 'stale': False}
        uzs = rows[hotels['uzs'].id]
        assert (uzs['base_price_uzs_approx'], uzs['uzs_rate']) == ('650000.00', None)

    def test_one_rate_lookup_per_request(self, hotels):
        _rate()
        with CaptureQueriesContext(connection) as queries:
            _search()
        rate_queries = [q for q in queries.captured_queries if 'exchange_rates' in q['sql']]
        assert len(rate_queries) == 1

    def test_no_rate_yet(self, hotels):
        row = _search()[hotels['usd'][0].id]
        assert (row['base_price_uzs_approx'], row['uzs_rate']) == (None, None)

    def test_stale_rate_is_flagged(self, hotels):
        _rate(days_old=5)
        assert _search()[hotels['usd'][0].id]['uzs_rate']['stale'] is True


@pytest.mark.django_db
class TestPropertyPages:

    def test_detail(self, hotels):
        _rate()
        data = APIClient().get(f"/api/v1/properties/{hotels['usd'][1].id}/").data
        assert (data['base_price'], data['base_price_uzs_approx']) == ('101.00', '1189068.00')  # 1 189 067.95
        assert data['uzs_rate']['rate'] == '11772.950000'

    def test_availability(self, hotels):
        _rate()
        data = APIClient().get(f"/api/v1/properties/{hotels['uzs'].id}/availability/").data
        assert (data['base_price_uzs_approx'], data['uzs_rate']) == ('650000.00', None)
