"""
R6: guests pay the booking's UZS snapshot. Payme counts in tiyin (1 so'm = 100 tiyin,
Merchant API "Сумма платежа (в тийинах)"), Click in so'm as a decimal ("1000.0"). We
store whole so'm and convert only inside the adapters, so every amount check compares
so'm with so'm.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking
from bookings.tests.test_quote import stay  # noqa: F401  (fixture: USD property, 60/69 USD nights)
from currency.cbu import tashkent_today
from currency.models import ExchangeRate
from payments.adapters import ClickAdapter, PaymeAdapter, get_payment_adapter
from payments.models import PaymentAuditLog, PaymentTransaction

RATE = Decimal('11772.95')
CHARGE = Decimal('2225088')          # 189.00 USD x 11772.95, rounded once
SECRET = 'r6-webhook-secret'
TRANSACTIONS_URL = '/api/v1/payments/transactions/'


def _rate(rate=RATE, days=0):
    return ExchangeRate.objects.create(currency='USD', rate=rate, nominal=1, source='cbu.uz', status='accepted',
                                       rate_date=tashkent_today() + timedelta(days=days))


@pytest.fixture
def booked(stay):
    """A USD-priced pending booking made through the API at RATE."""
    _rate()
    client = APIClient()
    client.force_authenticate(user=stay['guest'])
    response = client.post('/api/v1/bookings/', {
        'property_id': stay['property'].id, 'room_type_id': stay['room'].id, 'rate_plan_id': stay['rate'].id,
        'check_in': (stay['start'] + timedelta(days=1)).isoformat(),
        'check_out': (stay['start'] + timedelta(days=4)).isoformat(), 'guest_count': 1,
    }, format='json')
    assert response.status_code == 201, response.data
    return {'client': client, 'booking': Booking.objects.get(pk=response.data['id']), **stay}


def _pay(booked, key, provider='payme', **body):
    data = {'idempotency_key': key, 'booking': booked['booking'].id, 'provider': provider,
            'amount': str(CHARGE), 'currency': 'UZS'}
    data.update(body)
    return booked['client'].post(TRANSACTIONS_URL, data, format='json')


def _details(response):
    return response.data['error']['details']


@pytest.mark.django_db
class TestPaymentMustEqualTheSnapshot:

    def test_uzs_snapshot_amount_is_accepted(self, booked):
        response = _pay(booked, 'k-ok')

        assert response.status_code == 201, response.data
        tx = PaymentTransaction.objects.get(idempotency_key='k-ok')
        assert (tx.amount, tx.currency) == (CHARGE, 'UZS')

    def test_usd_total_is_rejected(self, booked):
        response = _pay(booked, 'k-usd', amount='189.00', currency='USD')
        assert response.status_code == 400
        assert not PaymentTransaction.objects.exists()

    def test_usd_currency_with_the_uzs_amount_is_rejected(self, booked):
        response = _pay(booked, 'k-cur', currency='USD')
        assert response.status_code == 400
        assert 'currency' in _details(response)

    def test_usd_amount_labelled_uzs_is_rejected(self, booked):
        response = _pay(booked, 'k-amt', amount='189.00')
        assert response.status_code == 400
        assert 'amount' in _details(response)

    def test_new_rate_after_booking_does_not_change_what_is_paid(self, booked):
        _rate(Decimal('12500'), days=1)
        ExchangeRate.objects.create(currency='USD', rate=Decimal('12000'), nominal=1, source='manual',
                                    status='accepted', rate_date=tashkent_today())

        assert _pay(booked, 'k-old-rate').status_code == 201
        assert _pay(booked, 'k-new-rate', amount=str((Decimal('189') * Decimal('12000')))).status_code == 400


class TestAdapterUnits:

    def test_payme_works_in_tiyin(self):
        adapter = PaymeAdapter()
        assert adapter.to_provider_amount(Decimal('2225088')) == 222508800
        assert adapter.to_provider_amount(Decimal('2225088.00')) == 222508800
        assert adapter.from_provider_amount(222508800) == Decimal('2225088')
        assert adapter.from_provider_amount('222508800') == Decimal('2225088')

    def test_payme_refuses_fractions_and_garbage(self):
        adapter = PaymeAdapter()
        with pytest.raises(ValueError):
            adapter.to_provider_amount(Decimal('2225088.50'))
        with pytest.raises(TypeError):
            adapter.to_provider_amount(2225088.0)
        for bad in ('2225088.00', '-1', '', None, 1.5, True):
            assert adapter.from_provider_amount(bad) is None

    def test_click_works_in_som(self):
        adapter = ClickAdapter()
        assert adapter.to_provider_amount(Decimal('2225088')) == '2225088.00'
        assert adapter.from_provider_amount('2225088.0') == Decimal('2225088')
        assert adapter.from_provider_amount('2225088.00') == Decimal('2225088')
        assert adapter.from_provider_amount(2225088) == Decimal('2225088')
        for bad in ('abc', '', None, 'NaN', '-5', True):
            assert adapter.from_provider_amount(bad) is None

    def test_click_never_sends_a_float(self):
        with pytest.raises(TypeError):
            ClickAdapter().to_provider_amount(2225088.0)


@pytest.mark.django_db
class TestWebhookComparesSomWithSom:

    def _tx(self, booked, provider):
        response = _pay(booked, f'k-{provider}', provider=provider)
        assert response.status_code == 201, response.data
        tx = PaymentTransaction.objects.get(idempotency_key=f'k-{provider}')
        PaymentTransaction.objects.filter(pk=tx.pk).update(provider_transaction_id=f'txn-{provider}')
        return tx

    def _webhook(self, provider, event_id, amount):
        adapter = get_payment_adapter(provider)
        payload = {'transaction_id': f'txn-{provider}', 'status': 'completed', 'amount': amount, 'currency': 'UZS',
                   'timestamp': int(timezone.now().timestamp())}
        if provider == 'payme':
            payload['id'] = event_id
            signature = adapter.generate_signature(payload, SECRET)
        else:
            payload['payment_id'] = event_id
            signature = adapter._generate_click_signature(payload, SECRET)
        setting = 'PAYME_SECRET_KEY' if provider == 'payme' else 'CLICK_SECRET_KEY'
        from django.test import override_settings
        with override_settings(**{setting: SECRET}):
            return APIClient().post(f'/api/v1/payments/webhook/{provider}/', payload, format='json',
                                    HTTP_X_SIGNATURE=signature)

    def _status(self, tx):
        tx.refresh_from_db()
        return tx.status, Booking.objects.get(pk=tx.booking_id).status

    def test_payme_tiyin_amount_confirms(self, booked):
        tx = self._tx(booked, 'payme')
        assert self._webhook('payme', 'evt-1', 222508800).status_code == 200
        assert self._status(tx) == ('completed', 'confirmed')

    def test_payme_amount_in_som_is_a_mismatch(self, booked):
        tx = self._tx(booked, 'payme')
        self._webhook('payme', 'evt-2', 2225088)
        assert self._status(tx)[0] in ('pending', 'processing')
        assert Booking.objects.get(pk=tx.booking_id).status == 'pending'

    def test_click_som_amount_confirms(self, booked):
        tx = self._tx(booked, 'click')
        assert self._webhook('click', 'evt-3', '2225088.00').status_code == 200
        assert self._status(tx) == ('completed', 'confirmed')

    def test_click_amount_in_tiyin_is_a_mismatch(self, booked):
        tx = self._tx(booked, 'click')
        self._webhook('click', 'evt-4', '222508800')
        assert self._status(tx)[0] in ('pending', 'processing')
        assert Booking.objects.get(pk=tx.booking_id).status == 'pending'


@pytest.mark.django_db
class TestRefundsUseThePaidAmount:

    def _paid(self, booked):
        assert _pay(booked, 'k-paid').status_code == 201
        tx = PaymentTransaction.objects.get(idempotency_key='k-paid')
        PaymentTransaction.objects.filter(pk=tx.pk).update(status='completed')
        Booking.objects.filter(pk=tx.booking_id).update(status='confirmed', payment_status='paid')
        return tx

    def _refund(self, booked, tx, body=None):
        from users.models import User
        staff = User.objects.create_user(email='staff-r6@example.com', password='StaffPassword#123', is_staff=True)
        client = APIClient()
        client.force_authenticate(user=staff)
        return client.post(f'{TRANSACTIONS_URL}{tx.id}/refund/', body or {}, format='json')

    def test_full_refund_is_the_uzs_snapshot_even_after_the_rate_moved(self, booked):
        tx = self._paid(booked)
        _rate(Decimal('12900'), days=1)

        response = self._refund(booked, tx)

        assert response.status_code == 200, response.data
        tx.refresh_from_db()
        assert tx.status == 'refunded'
        refund = PaymentAuditLog.objects.get(action='payment_refunded', payment_transaction=tx)
        assert refund.details['refund_amount'] == '2225088.00'

    def test_partial_uzs_refund_with_tiyin_is_rejected(self, booked):
        tx = self._paid(booked)
        response = self._refund(booked, tx, {'amount': '1000.50'})
        assert response.status_code == 400
        tx.refresh_from_db()
        assert tx.status == 'completed'

    def test_partial_uzs_refund_in_whole_som(self, booked):
        tx = self._paid(booked)
        response = self._refund(booked, tx, {'amount': '1000'})
        assert response.status_code == 200, response.data
        tx.refresh_from_db()
        assert tx.status == 'partially_refunded'
