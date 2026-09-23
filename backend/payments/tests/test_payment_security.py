"""
Security tests for the payment API (audit findings #4, #5, #6, #14, #15, #16).
"""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from bookings.models import Booking
from payments.models import PaymentTransaction
from properties.models import Property, PropertyType

TRANSACTIONS_URL = '/api/v1/payments/transactions/'


def error_details(response):
    """Field errors from the project's standard error envelope."""
    return response.data['error']['details']


class PaymentSecurityTestBase(TestCase):
    """Two guests, each with a pending booking, and a staff user."""

    def setUp(self):
        from users.models import User

        self.guest = User.objects.create_user(email='guest@example.com', password='testpass123')
        self.other_guest = User.objects.create_user(email='other@example.com', password='testpass123')
        self.staff = User.objects.create_user(email='staff@example.com', password='testpass123', is_staff=True)

        property_type = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.property = Property.objects.create(
            owner=self.staff, property_type=property_type, status='active',
            max_guests=4, bedrooms=1, bathrooms=1, city='Tashkent', country='Uzbekistan',
            base_price=Decimal('100.00'), currency='USD'
        )
        self.booking = self._create_booking(self.guest, 'GST001')
        self.other_booking = self._create_booking(self.other_guest, 'OTH001')

        self.client = APIClient()
        self.client.force_authenticate(user=self.guest)

    def _create_booking(self, guest, code):
        check_in = timezone.now().date() + timedelta(days=7)
        return Booking.objects.create(
            guest=guest, property=self.property, status='pending', payment_status='pending',
            check_in=check_in, check_out=check_in + timedelta(days=3), number_of_nights=3,
            guest_count=2, total_price=Decimal('300.00'), currency='USD', confirmation_code=code
        )

    def _create_transaction(self, booking, key, tx_status='processing', provider_transaction_id=None):
        return PaymentTransaction.objects.create(
            idempotency_key=key, booking=booking, provider='payme',
            amount=booking.total_price, currency='USD', status=tx_status,
            provider_transaction_id=provider_transaction_id or f'txn_{key}'
        )

    def _payment_data(self, booking, key, **extra):
        data = {
            'idempotency_key': key, 'booking': booking.id, 'provider': 'payme',
            'amount': str(booking.total_price), 'currency': 'USD',
        }
        data.update(extra)
        return data


class TestTransactionOwnership(PaymentSecurityTestBase):
    """#16: transactions belong to the booking's guest and are not editable."""

    def test_cannot_create_payment_for_another_users_booking(self):
        response = self.client.post(TRANSACTIONS_URL, self._payment_data(self.other_booking, 'k-other'), format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'booking' in error_details(response)
        assert not PaymentTransaction.objects.filter(booking=self.other_booking).exists()

    def test_transactions_cannot_be_updated_or_deleted(self):
        tx = self._create_transaction(self.booking, 'k-edit', tx_status='pending')
        url = f'{TRANSACTIONS_URL}{tx.id}/'

        patch = self.client.patch(url, {'amount': '0.01', 'booking': self.other_booking.id}, format='json')
        put = self.client.put(url, self._payment_data(self.booking, 'k-edit'), format='json')
        delete = self.client.delete(url)

        assert patch.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert put.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert delete.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        tx.refresh_from_db()
        assert tx.amount == Decimal('300.00') and tx.booking_id == self.booking.id

    def test_payment_method_token_is_never_returned(self):
        create = self.client.post(
            TRANSACTIONS_URL, self._payment_data(self.booking, 'k-token', payment_method_token='secret-tok'),
            format='json'
        )
        detail = self.client.get(f"{TRANSACTIONS_URL}{create.data['id']}/")

        assert create.status_code == status.HTTP_201_CREATED
        assert 'payment_method_token' not in create.data
        assert 'payment_method_token' not in detail.data
        assert PaymentTransaction.objects.get(id=create.data['id']).payment_method_token == 'secret-tok'

    def test_client_ip_and_user_agent_come_from_request_not_body(self):
        response = self.client.post(
            TRANSACTIONS_URL,
            self._payment_data(self.booking, 'k-ip', client_ip='6.6.6.6', user_agent='spoofed'),
            format='json', REMOTE_ADDR='10.0.0.5', HTTP_USER_AGENT='RealBrowser/1.0'
        )

        tx = PaymentTransaction.objects.get(id=response.data['id'])
        assert tx.client_ip == '10.0.0.5'
        assert tx.user_agent == 'RealBrowser/1.0'


class TestIdempotency(PaymentSecurityTestBase):
    """#32: the same key returns the original transaction to its owner only."""

    def test_repeating_request_returns_original_transaction(self):
        first = self.client.post(TRANSACTIONS_URL, self._payment_data(self.booking, 'k-idem'), format='json')
        second = self.client.post(TRANSACTIONS_URL, self._payment_data(self.booking, 'k-idem'), format='json')

        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_200_OK
        assert second.data['id'] == first.data['id']
        assert PaymentTransaction.objects.filter(idempotency_key='k-idem').count() == 1

    def test_other_users_key_is_rejected_without_leaking_transaction(self):
        other_tx = self._create_transaction(self.other_booking, 'k-shared')

        response = self.client.post(TRANSACTIONS_URL, self._payment_data(self.booking, 'k-shared'), format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'idempotency_key' in error_details(response)
        assert str(other_tx.id) not in str(response.data)
        assert 'provider_transaction_id' not in response.data


class TestWebhookEventVisibility(PaymentSecurityTestBase):
    """#14: webhook events (payloads with PII) are visible to staff only."""

    def setUp(self):
        super().setUp()
        from payments.models import WebhookEvent

        self.event = WebhookEvent.objects.create(
            provider='payme', provider_event_id='evt-1', payload={'phone': '+998900000000'},
            signature='sig', status='processed'
        )

    def test_regular_user_cannot_list_or_read_webhook_events(self):
        listing = self.client.get('/api/v1/payments/webhooks/')
        detail = self.client.get(f'/api/v1/payments/webhooks/{self.event.id}/')

        assert listing.status_code == status.HTTP_403_FORBIDDEN
        assert detail.status_code == status.HTTP_403_FORBIDDEN

    def test_staff_can_list_webhook_events(self):
        self.client.force_authenticate(user=self.staff)

        response = self.client.get('/api/v1/payments/webhooks/')

        assert response.status_code == status.HTTP_200_OK
        assert self.event.id in [event['id'] for event in response.data['results']]
