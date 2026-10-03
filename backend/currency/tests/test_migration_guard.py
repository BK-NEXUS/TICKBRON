"""
R6 decision B: the first R6 migration stops, before changing anything, if a
property is priced in a currency other than the supported ones, and says which
properties and how to fix them.
"""
from decimal import Decimal

import pytest
from django.apps import apps as django_apps

from currency.guard import check_property_currencies
from properties.models import Property, PropertyType
from users.models import User


def _property(currency, city='Tashkent'):
    return Property.objects.create(
        owner=User.objects.create_user(email=f'{currency}{city}@example.com', password='x'),
        property_type=PropertyType.objects.get_or_create(name='Hotel', slug='hotel')[0],
        status='active', max_guests=2, bedrooms=1, bathrooms=1, city=city, country='X',
        base_price=Decimal('10'), currency=currency,
    )


@pytest.mark.django_db
def test_supported_currencies_pass():
    _property('USD')
    _property('UZS')
    check_property_currencies(django_apps, None)


@pytest.mark.django_db
def test_other_currency_stops_with_a_list_and_a_fix():
    eur = _property('EUR', city='Istanbul')
    _property('USD')

    with pytest.raises(RuntimeError) as error:
        check_property_currencies(django_apps, None)

    message = str(error.value)
    assert f'id={eur.id}' in message and 'EUR' in message
    assert 'USD, UZS' in message or 'UZS, USD' in message
    assert 'seed_demo_stats' in message and 'currency' in message


@pytest.mark.django_db
def test_child_rows_with_other_currencies_are_listed_too():
    from properties.models import RatePlan, RoomType
    prop = _property('USD')
    room = RoomType.objects.create(property=prop, name='Std', slug='std', base_occupancy=1, max_occupancy=2,
                                   base_price=10, currency='EUR', total_rooms=1)
    RatePlan.objects.create(room_type=room, name='R', slug='r', rate_type='standard', base_price=10,
                            currency='EUR', min_nights=1, is_active=True)

    with pytest.raises(RuntimeError) as error:
        check_property_currencies(django_apps, None)
    assert f'room type id={room.id}' in str(error.value)
