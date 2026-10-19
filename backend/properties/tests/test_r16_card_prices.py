"""
R16 slice 2: every hotel card (search, map, home promotions) carries a "from" price in every currency, and the
calendar rows of the availability endpoint carry the night price in every currency.

A hotel's "from" price in a currency = the lowest price of its active rate plans in that currency (the owner's own
price, or a conversion when the owner entered none). `base_price` and `currency` stay as they were (filters use them).
Fixture `stay`: a USD hotel, plan "Standard Rate" 60 USD, nights +2 = 69 USD.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from bookings.tests.test_quote import stay  # noqa: F401  (fixture)
from currency.cbu import tashkent_today
from currency.models import ExchangeRate
from properties.models import RatePlan, RatePlanPrice

pytestmark = pytest.mark.django_db


def prices(stay, plan=None, **entered):
    for code, amount in entered.items():
        RatePlanPrice.objects.create(rate_plan=plan or stay['rate'], currency=code, amount=Decimal(amount))


def second_plan(stay, **extra):
    return RatePlan.objects.create(
        room_type=stay['room'], name='Cheap Rate', slug='cheap', rate_type='standard',
        base_price=Decimal('54.00'), currency='USD', min_nights=1, max_nights=7, is_active=True, **extra)


def card(stay):
    response = APIClient().get('/api/v1/properties/search/', {'location': 'Tashkent'})
    assert response.status_code == 200, response.data
    return next(row for row in response.data['results'] if row['id'] == stay['property'].id)


def kzt_rate(rate='24.50'):
    ExchangeRate.objects.create(currency='KZT', rate=Decimal(rate), nominal=1, source='cbu.uz', status='accepted',
                                rate_date=tashkent_today())


class TestCardFromPrice:

    def test_lowest_owner_price_per_currency_across_the_plans(self, stay):
        prices(stay, UZS='750000', KZT='27000', RUB='5400')
        cheap = second_plan(stay)
        prices(stay, plan=cheap, UZS='800000', KZT='24000', RUB='5000')
        data = card(stay)
        assert data['prices']['USD'] == {'amount': '54.00', 'source': 'main'}
        assert data['prices']['UZS'] == {'amount': '750000.00', 'source': 'owner'}
        assert data['prices']['KZT'] == {'amount': '24000.00', 'source': 'owner'}
        assert data['prices']['RUB'] == {'amount': '5000.00', 'source': 'owner'}

    def test_base_price_and_currency_are_unchanged(self, stay):
        prices(stay, UZS='750000')
        data = card(stay)
        assert (data['base_price'], data['currency']) == ('60.00', 'USD')

    def test_a_currency_without_an_owner_price_is_converted(self, stay):
        kzt_rate('24.50')
        prices(stay, UZS='750000')
        data = card(stay)
        # 60 USD x 12000 / 24.50 = 29 387.76 -> 29 388
        assert data['prices']['KZT'] == {'amount': '29388.00', 'source': 'converted'}
        assert data['prices']['UZS']['source'] == 'owner'

    def test_no_rate_means_no_amount_for_a_converted_currency(self, stay):
        data = card(stay)
        assert data['prices']['RUB'] == {'amount': None, 'source': 'converted'}

    def test_inactive_and_deleted_plans_do_not_count(self, stay):
        inactive = second_plan(stay)
        RatePlan.objects.filter(pk=inactive.pk).update(is_active=False)
        deleted = RatePlan.objects.create(
            room_type=stay['room'], name='Gone', slug='gone', rate_type='standard', base_price=Decimal('10.00'),
            currency='USD', min_nights=1, max_nights=7, is_active=True, is_deleted=True)
        assert deleted.is_deleted
        assert card(stay)['prices']['USD']['amount'] == '60.00'

    def test_a_hotel_without_rate_plans_uses_its_own_price(self, stay):
        RatePlan.objects.filter(room_type=stay['room']).delete()
        kzt_rate('24.50')
        data = card(stay)
        assert data['prices']['USD'] == {'amount': '60.00', 'source': 'main'}
        assert data['prices']['KZT'] == {'amount': '29388.00', 'source': 'converted'}


class TestCalendarRows:

    def rows(self, stay):
        response = APIClient().get(f"/api/v1/properties/{stay['property'].id}/availability/",
                                   {'check_in': stay['start'].isoformat(),
                                    'check_out': (stay['start'] + timedelta(days=5)).isoformat()})
        assert response.status_code == 200, response.data
        plan = response.data['room_types'][0]['rate_plans'][0]
        return plan, {row['date']: row for row in plan['date_inventory']}

    def test_each_night_in_every_currency_with_the_plans_ratio(self, stay):
        prices(stay, UZS='750000', KZT='27000', RUB='5400')
        plan, rows = self.rows(stay)
        normal = rows[(stay['start'] + timedelta(days=1)).isoformat()]['prices']
        special = rows[(stay['start'] + timedelta(days=2)).isoformat()]['prices']     # 69 USD (+15%)
        base_night = rows[(stay['start'] + timedelta(days=3)).isoformat()]['prices']  # no own price: the plan's
        assert normal == {'USD': '60.00', 'UZS': '750000.00', 'KZT': '27000.00', 'RUB': '5400.00'}
        assert special == {'USD': '69.00', 'UZS': '862500.00', 'KZT': '31050.00', 'RUB': '6210.00'}
        assert base_night == normal
        assert plan['prices']['UZS'] == {'amount': '750000.00', 'source': 'owner'}

    def test_a_converted_currency_has_amounts_only_with_a_rate(self, stay):
        kzt_rate('24.50')
        _, rows = self.rows(stay)
        night = rows[(stay['start'] + timedelta(days=1)).isoformat()]['prices']
        assert night['KZT'] == '29388.00'
        assert night['RUB'] is None
