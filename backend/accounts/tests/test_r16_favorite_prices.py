"""
R16: a favorite carries the "from" price of its hotel in every currency (`property_prices`, the same list a hotel
card has: the lowest price of the active rate plans, the owner's own or a conversion). `property_base_price` and
`property_currency` stay as they were.
"""
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from accounts.models import Favorite
from currency.cbu import tashkent_today
from currency.models import ExchangeRate
from properties.models import Property, PropertyType, RatePlan, RatePlanPrice, RoomType
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def guest():
    return User.objects.create_user(email='fav@example.com', password='Passw0rd#12345')


def hotel(guest, number, plan_price='60.00', owner_prices=None):
    prop = Property.objects.create(
        owner=guest, property_type=PropertyType.objects.get_or_create(name='Hotel', slug='hotel')[0], status='active',
        max_guests=2, bedrooms=1, bathrooms=1, address_line1=f'{number} Street', city='Bukhara',
        country='Uzbekistan', base_price=60, currency='USD')
    room = RoomType.objects.create(property=prop, name='Std', slug='std', base_occupancy=2, max_occupancy=2,
                                   base_price=60, currency='USD', total_rooms=2)
    plan = RatePlan.objects.create(room_type=room, name='Rate', slug='rate', rate_type='standard',
                                   base_price=Decimal(plan_price), currency='USD', min_nights=1, is_active=True)
    for code, amount in (owner_prices or {}).items():
        RatePlanPrice.objects.create(rate_plan=plan, currency=code, amount=Decimal(amount))
    Favorite.objects.create(user=guest, property=prop)
    return prop


def favorites(guest):
    client = APIClient()
    client.force_authenticate(user=guest)
    with CaptureQueriesContext(connection) as queries:
        response = client.get('/api/v1/me/favorites/')
    assert response.status_code == 200, response.data
    return response.data['results'], queries


def test_the_from_price_in_every_currency(guest):
    ExchangeRate.objects.create(currency='KZT', rate=Decimal('24.50'), nominal=1, source='cbu.uz', status='accepted',
                                rate_date=tashkent_today())
    hotel(guest, 1, owner_prices={'UZS': '750000', 'KZT': '27000', 'RUB': '5400'})
    item = favorites(guest)[0][0]
    assert item['property_prices']['USD'] == {'amount': '60.00', 'source': 'main'}
    assert item['property_prices']['UZS'] == {'amount': '750000.00', 'source': 'owner'}
    assert item['property_prices']['KZT'] == {'amount': '27000.00', 'source': 'owner'}
    assert (item['property_base_price'], item['property_currency']) == ('60.00', 'USD')


def test_a_currency_without_an_owner_price_is_converted_or_empty(guest):
    ExchangeRate.objects.create(currency='KZT', rate=Decimal('24.50'), nominal=1, source='cbu.uz', status='accepted',
                                rate_date=tashkent_today())
    hotel(guest, 1)
    prices = favorites(guest)[0][0]['property_prices']
    assert prices['KZT'] == {'amount': '29388.00', 'source': 'converted'}
    assert prices['RUB'] == {'amount': None, 'source': 'converted'}   # no ruble rate yet


def test_the_number_of_queries_does_not_grow_with_the_favorites_and_rates_are_read_once(guest):
    hotel(guest, 1, owner_prices={'UZS': '750000'})
    _, few = favorites(guest)
    for number in range(2, 8):
        hotel(guest, number, owner_prices={'UZS': '700000'})
    items, many = favorites(guest)
    assert len(items) == 7
    assert len(many) == len(few)
    assert len([q for q in many.captured_queries if 'exchange_rates' in q['sql']]) == 1
