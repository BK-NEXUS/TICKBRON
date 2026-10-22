"""
R16 slice 1: the hotel owner's own price per currency (RatePlanPrice) decides what a guest
sees and what is charged; a currency without an owner price is converted at the CBU rate.

Fixture `stay` (test_quote.py): a USD hotel, rate plan 60 USD, nights +1 = 60, +2 = 69, +3 = base 60
(stay of nights 1-3 = 189 USD). Default test USD rate: 12000 so'm.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from bookings.models import Booking
from bookings.pricing import price_list, quote_stay
from bookings.tests.test_quote import stay  # noqa: F401  (fixture)
from currency.cbu import tashkent_today
from currency.models import ExchangeRate
from properties.models import RatePlanPrice

pytestmark = pytest.mark.django_db

# Owner prices for the 60 USD base: 750 000 so'm, 27 000 tenge, 5 400 rubles
OWNER = {'UZS': '750000', 'KZT': '27000', 'RUB': '5400'}


def owner_prices(stay, **only):
    for code, amount in (only or OWNER).items():
        RatePlanPrice.objects.create(rate_plan=stay['rate'], currency=code, amount=Decimal(amount))


def kzt_rate(rate='24.50'):
    ExchangeRate.objects.create(currency='KZT', rate=Decimal(rate), nominal=1, source='cbu.uz',
                                status='accepted', rate_date=tashkent_today())


def quote_for(stay, first=1, last=4, rooms=1):
    return quote_stay(stay['rate'], stay['start'] + timedelta(days=first), stay['start'] + timedelta(days=last), rooms)


def api_quote(stay, first=1, last=4, **params):
    params = {
        'room_type_id': stay['room'].id, 'rate_plan_id': stay['rate'].id,
        'check_in': (stay['start'] + timedelta(days=first)).isoformat(),
        'check_out': (stay['start'] + timedelta(days=last)).isoformat(), **params,
    }
    return APIClient().get(f"/api/v1/properties/{stay['property'].id}/quote/", params)


def book(stay, first=1, last=4):
    client = APIClient()
    client.force_authenticate(user=stay['guest'])
    return client.post('/api/v1/bookings/', {
        'property_id': stay['property'].id, 'room_type_id': stay['room'].id, 'rate_plan_id': stay['rate'].id,
        'check_in': (stay['start'] + timedelta(days=first)).isoformat(),
        'check_out': (stay['start'] + timedelta(days=last)).isoformat(), 'guest_count': 1, 'expected_arrival_time': '14:00',
    }, format='json')


class TestStayTotalInACurrency:

    def test_main_currency_is_the_plain_total(self, stay):
        assert quote_for(stay).total_in('USD') == (Decimal('189.00'), 'main')

    def test_owner_price_is_used_and_a_special_night_keeps_the_ratio(self, stay):
        owner_prices(stay)
        quote = quote_for(stay)
        # 60 -> 750000, 69 (+15%) -> 862500, base night -> 750000
        assert quote.total_in('UZS') == (Decimal('2362500'), 'owner')
        assert quote.total_in('KZT') == (Decimal('85050'), 'owner')    # 27000 + 31050 + 27000
        assert quote.total_in('RUB') == (Decimal('17010'), 'owner')    # 5400 + 6210 + 5400

    def test_rooms_multiply_and_the_total_is_rounded_once(self, stay):
        owner_prices(stay, UZS='750001')
        quote = quote_for(stay, rooms=2)
        # nightly sum 750001 + 862501.15 + 750001 = 2 362 503.15, times 2 = 4 725 006.30 -> 4 725 006
        assert quote.total_in('UZS') == (Decimal('4725006'), 'owner')

    def test_a_currency_without_an_owner_price_is_converted_at_the_cbu_rates(self, stay):
        kzt_rate('24.50')
        quote = quote_for(stay)
        # 189 USD x 12000 / 24.50 = 92 571.43 -> 92 571 tenge
        assert quote.total_in('KZT') == (Decimal('92571'), 'converted')
        assert quote.total_in('UZS') == (Decimal('2268000'), 'converted')

    def test_no_rate_and_no_owner_price_means_no_answer(self, stay):
        assert quote_for(stay).total_in('RUB') == (None, 'converted')
        assert quote_for(stay).nights_in('RUB') is None

    def test_nights_in_a_currency_are_rounded_for_display(self, stay):
        owner_prices(stay)
        rows = quote_for(stay).nights_in('UZS')
        assert [price for _, price in rows] == [Decimal('750000'), Decimal('862500'), Decimal('750000')]

    def test_price_list_has_every_supported_currency(self, stay):
        owner_prices(stay, UZS='750000')
        listing = price_list(stay['rate'])
        assert listing['USD'] == {'amount': '60.00', 'source': 'main'}
        assert listing['UZS'] == {'amount': '750000.00', 'source': 'owner'}
        assert listing['KZT'] == {'amount': None, 'source': 'converted'}   # no KZT rate in the database
        kzt_rate('24.50')
        assert price_list(stay['rate'])['KZT'] == {'amount': '29388.00', 'source': 'converted'}


class TestPublicQuote:

    def test_without_currency_nothing_changes_for_the_guest(self, stay):
        response = api_quote(stay)
        assert response.status_code == 200
        assert (response.data['currency'], response.data['total_price']) == ('USD', '189.00')
        assert response.data['price_source'] == 'main'

    def test_requested_currency_gets_the_owner_price(self, stay):
        owner_prices(stay)
        response = api_quote(stay, currency='KZT')
        assert response.status_code == 200
        assert (response.data['currency'], response.data['total_price']) == ('KZT', '85050.00')
        assert response.data['price_source'] == 'owner'
        assert [night['price'] for night in response.data['nights']] == ['27000.00', '31050.00', '27000.00']

    def test_converted_price_is_marked(self, stay):
        kzt_rate('24.50')
        response = api_quote(stay, currency='KZT')
        assert (response.data['total_price'], response.data['price_source']) == ('92571.00', 'converted')

    def test_no_rate_for_a_converted_price_is_503(self, stay):
        response = api_quote(stay, currency='RUB')
        assert response.status_code == 503
        assert response.data['code'] == 'exchange_rate_unavailable'

    def test_unknown_currency_is_400(self, stay):
        response = api_quote(stay, currency='EUR')
        assert response.status_code == 400
        assert 'currency' in str(response.data)

    def test_the_so_m_the_guest_pays_is_the_owners_so_m_price(self, stay):
        owner_prices(stay)
        response = api_quote(stay)    # asked in dollars; payment is in so'm
        assert response.data['uzs_total'] == '2362500.00'
        assert response.data['exchange_rate'] is None


class TestBookingCharge:

    def test_the_charge_is_the_owners_so_m_price_not_a_conversion(self, stay):
        owner_prices(stay)
        response = book(stay)
        assert response.status_code == 201, response.data
        booking = Booking.objects.get()
        assert (booking.total_price, booking.currency) == (Decimal('189.00'), 'USD')
        assert (booking.charge_currency, booking.charge_amount) == ('UZS', Decimal('2362500'))
        assert booking.exchange_rate_source == 'owner'
        assert booking.exchange_rate == Decimal('12500.000000')   # 2 362 500 / 189, informational
        assert booking.exchange_rate_date is None and booking.exchange_rate_stale is False

    @pytest.mark.no_default_exchange_rate
    def test_it_needs_no_exchange_rate_at_all(self, stay):
        assert not ExchangeRate.objects.exists()
        owner_prices(stay)
        assert book(stay).status_code == 201

    @pytest.mark.no_default_exchange_rate
    def test_without_an_owner_so_m_price_the_cbu_conversion_is_unchanged(self, stay):
        ExchangeRate.objects.create(currency='USD', rate=Decimal('11772.95'), nominal=1, source='cbu.uz',
                                    status='accepted', rate_date=tashkent_today())
        owner_prices(stay, KZT='27000')     # a tenge price does not change the so'm charge
        assert book(stay).status_code == 201
        booking = Booking.objects.get()
        assert booking.charge_amount == Decimal('2225088')
        assert booking.exchange_rate_source == 'cbu.uz'

    def test_a_uzs_hotel_is_charged_as_before(self, stay):
        from properties.models import DateInventory, Property, RatePlan, RoomType
        Property.objects.filter(pk=stay['property'].pk).update(currency='UZS')
        RoomType.objects.filter(pk=stay['room'].pk).update(currency='UZS')
        RatePlan.objects.filter(pk=stay['rate'].pk).update(currency='UZS', base_price=Decimal('700000'))
        DateInventory.objects.filter(rate_plan=stay['rate']).update(currency='UZS', price=Decimal('700000'))
        assert book(stay).status_code == 201
        booking = Booking.objects.get()
        assert (booking.charge_amount, booking.exchange_rate_source) == (booking.total_price, 'identity')


class TestHotelPage:

    def test_every_rate_plan_lists_its_price_in_every_currency(self, stay):
        owner_prices(stay, UZS='750000')
        kzt_rate('24.50')
        response = APIClient().get(f"/api/v1/properties/{stay['property'].id}/")
        assert response.status_code == 200
        prices = response.data['room_types'][0]['rate_plans'][0]['prices']
        assert prices['USD'] == {'amount': '60.00', 'source': 'main'}
        assert prices['UZS'] == {'amount': '750000.00', 'source': 'owner'}
        assert prices['KZT'] == {'amount': '29388.00', 'source': 'converted'}
        assert prices['RUB'] == {'amount': None, 'source': 'converted'}   # no ruble rate yet
