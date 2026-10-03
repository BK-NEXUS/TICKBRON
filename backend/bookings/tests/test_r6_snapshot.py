"""
R6: every booking stores what the guest is charged: charge currency (UZS), the
UZS amount, the rate used, its date and source, and whether it was stale. Written
in the transaction that locks the inventory, from a database read of the rate,
and never changed afterwards.
"""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

import pytest
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking
from bookings.tests.test_quote import stay  # noqa: F401  (fixture: USD property, 60/69 USD nights)
from currency.models import ExchangeRate
from currency.cbu import tashkent_today
from properties.models import DateInventory, Property, RatePlan, RoomInventory, RoomType

RATE = Decimal('11772.95')


def _rate(rate=RATE, days_old=0):
    return ExchangeRate.objects.create(currency='USD', rate=rate, nominal=1, source='cbu.uz', status='accepted',
                                       rate_date=tashkent_today() - timedelta(days=days_old))


def _book(stay, first=1, last=4, **extra):
    client = APIClient()
    client.force_authenticate(user=stay['guest'])
    body = {
        'property_id': stay['property'].id, 'room_type_id': stay['room'].id, 'rate_plan_id': stay['rate'].id,
        'check_in': (stay['start'] + timedelta(days=first)).isoformat(),
        'check_out': (stay['start'] + timedelta(days=last)).isoformat(), 'guest_count': 1,
    }
    body.update(extra)
    return client.post('/api/v1/bookings/', body, format='json')


def _make_uzs(stay):
    Property.objects.filter(pk=stay['property'].pk).update(currency='UZS')
    RoomType.objects.filter(pk=stay['room'].pk).update(currency='UZS')
    RatePlan.objects.filter(pk=stay['rate'].pk).update(currency='UZS', base_price=Decimal('700000'))
    DateInventory.objects.filter(rate_plan=stay['rate']).update(currency='UZS', price=Decimal('700000'))


@pytest.mark.django_db
class TestSnapshotOnCreate:

    def test_usd_booking_is_charged_in_uzs_at_the_current_rate(self, stay):
        _rate()
        response = _book(stay)   # 60 + 69 + base 60 = 189.00 USD

        assert response.status_code == 201, response.data
        booking = Booking.objects.get()
        assert (booking.total_price, booking.currency) == (Decimal('189.00'), 'USD')
        assert booking.charge_currency == 'UZS'
        assert booking.charge_amount == Decimal('2225088')   # 189 x 11772.95 = 2 225 087.55 -> rounded once
        assert booking.exchange_rate == RATE
        assert booking.exchange_rate_date == tashkent_today()
        assert booking.exchange_rate_source == 'cbu.uz'
        assert booking.exchange_rate_stale is False
        assert response.data['charge_amount'] == '2225088.00'
        assert response.data['charge_currency'] == 'UZS'
        assert response.data['exchange_rate'] == {
            'rate': '11772.950000', 'date': tashkent_today().isoformat(), 'source': 'cbu.uz', 'stale': False}

    def test_uzs_booking_needs_no_rate(self, stay):
        _make_uzs(stay)
        response = _book(stay)

        assert response.status_code == 201, response.data
        booking = Booking.objects.get()
        assert (booking.currency, booking.total_price) == ('UZS', Decimal('2100000'))
        assert (booking.charge_currency, booking.charge_amount) == ('UZS', Decimal('2100000'))
        assert (booking.exchange_rate, booking.exchange_rate_source) == (Decimal('1'), 'identity')
        assert booking.exchange_rate_date is None

    def test_usd_booking_without_any_rate_is_refused_and_reserves_nothing(self, stay):
        rooms_before = list(RoomInventory.objects.values_list('date', 'booked_rooms'))
        response = _book(stay)

        assert response.status_code == 503
        assert response.data['code'] == 'exchange_rate_unavailable'
        assert not Booking.objects.exists()
        assert list(RoomInventory.objects.values_list('date', 'booked_rooms')) == rooms_before

    def test_stale_rate_is_used_and_flagged(self, stay):
        _rate(days_old=5)
        response = _book(stay)

        assert response.status_code == 201
        assert Booking.objects.get().exchange_rate_stale is True
        assert response.data['exchange_rate']['stale'] is True

    def test_client_sent_currency_rate_and_amounts_are_ignored(self, stay):
        _rate()
        response = _book(stay, currency='UZS', charge_currency='USD', charge_amount='1.00', exchange_rate='1',
                         total_price='1.00', uzs_total='1')

        assert response.status_code == 201
        booking = Booking.objects.get()
        assert (booking.currency, booking.total_price) == ('USD', Decimal('189.00'))
        assert (booking.charge_currency, booking.charge_amount, booking.exchange_rate) == \
            ('UZS', Decimal('2225088'), RATE)

    def test_rate_is_read_inside_the_transaction_that_locks_the_inventory(self, stay):
        _rate()
        from currency import rates
        seen = {}
        real = rates.current_rate

        def spy(currency, today=None):
            seen['atomic'] = connection.in_atomic_block
            seen['locked_before'] = any('FOR UPDATE' in q['sql'] and 'room_inventory' in q['sql']
                                        for q in connection.queries)
            return real(currency, today)

        with mock.patch('bookings.models.current_rate', side_effect=spy), \
                mock.patch.object(connection, 'force_debug_cursor', True):
            assert _book(stay).status_code == 201
        assert seen == {'atomic': True, 'locked_before': True}


@pytest.mark.django_db
class TestSnapshotNeverChanges:

    def test_new_rate_does_not_touch_existing_bookings(self, stay):
        _rate()
        _book(stay)
        before = Booking.objects.values('charge_amount', 'exchange_rate', 'exchange_rate_date').get()

        ExchangeRate.objects.create(currency='USD', rate=Decimal('12500'), nominal=1, source='cbu.uz',
                                    status='accepted', rate_date=tashkent_today() + timedelta(days=1))
        booking = Booking.objects.get()
        booking.confirm_booking()
        booking.cancel_booking('changed plans')

        assert Booking.objects.values('charge_amount', 'exchange_rate', 'exchange_rate_date').get() == before

    @pytest.mark.parametrize('field, value', [
        ('charge_amount', Decimal('1')), ('charge_currency', 'USD'), ('exchange_rate', Decimal('2')),
        ('exchange_rate_date', timezone.localdate() - timedelta(days=30)), ('exchange_rate_source', 'manual'),
        ('exchange_rate_stale', True), ('total_price', Decimal('1')), ('currency', 'UZS'),
    ])
    def test_saving_a_changed_snapshot_field_is_refused(self, stay, field, value):
        _rate()
        _book(stay)
        booking = Booking.objects.get()
        setattr(booking, field, value)

        with pytest.raises(PermissionError):
            booking.save()

    def test_other_fields_still_save(self, stay):
        _rate()
        _book(stay)
        booking = Booking.objects.get()
        booking.special_requests = 'Late arrival'
        booking.save()
        assert Booking.objects.get().special_requests == 'Late arrival'


@pytest.mark.django_db
class TestRowsCreatedOutsideTheBookingFlow:
    """Seeds and old code paths create Booking rows directly; they get an honest snapshot."""

    def _create(self, stay, currency, total):
        return Booking.objects.create(
            guest=stay['guest'], property=stay['property'], status='completed', payment_status='paid',
            check_in=stay['start'], check_out=stay['start'] + timedelta(days=1), number_of_nights=1,
            guest_count=1, total_price=Decimal(total), currency=currency, confirmation_code=f'X{currency}1',
        )

    def test_uzs_row_gets_the_identity_snapshot(self, stay):
        booking = self._create(stay, 'UZS', '700000')
        assert (booking.charge_currency, booking.charge_amount, booking.exchange_rate_source) == \
            ('UZS', Decimal('700000'), 'identity')

    def test_other_currency_row_is_marked_legacy_in_its_own_currency(self, stay):
        booking = self._create(stay, 'USD', '60.00')
        assert (booking.charge_currency, booking.charge_amount, booking.exchange_rate, booking.exchange_rate_source) \
            == ('USD', Decimal('60.00'), Decimal('1'), 'legacy')


@pytest.mark.django_db
class TestQuoteShowsBothAmounts:

    def _quote(self, stay):
        return APIClient().get(f"/api/v1/properties/{stay['property'].id}/quote/", {
            'room_type_id': stay['room'].id, 'rate_plan_id': stay['rate'].id,
            'check_in': (stay['start'] + timedelta(days=1)).isoformat(),
            'check_out': (stay['start'] + timedelta(days=4)).isoformat()})

    def test_usd_quote_has_the_uzs_total_that_will_be_charged(self, stay):
        _rate()
        data = self._quote(stay).data
        assert (data['total_price'], data['currency']) == ('189.00', 'USD')
        assert data['uzs_total'] == '2225088.00'
        assert data['exchange_rate']['rate'] == '11772.950000'
        assert data['uzs_total'] == f"{_book(stay).data['charge_amount']}"

    def test_usd_quote_without_rate_still_answers_in_usd(self, stay):
        data = self._quote(stay).data
        assert data['total_price'] == '189.00'
        assert data['uzs_total'] is None and data['exchange_rate'] is None

    def test_uzs_quote(self, stay):
        _make_uzs(stay)
        data = self._quote(stay).data
        assert (data['total_price'], data['currency'], data['uzs_total']) == ('2100000.00', 'UZS', '2100000.00')
        assert data['exchange_rate'] is None
