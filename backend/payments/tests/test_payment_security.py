"""
Security tests for the payment API (audit findings #4, #5, #6, #14, #15, #16).
"""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

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


class TestClientConfirm(PaymentSecurityTestBase):
    """#4: the client-side confirm is a local development mock only."""

    def _confirm(self, tx):
        return self.client.post(f'{TRANSACTIONS_URL}{tx.id}/confirm/')

    def test_confirm_forbidden_without_test_mode(self):
        tx = self._create_transaction(self.booking, 'k-c1')

        with self.settings(PAYMENT_TEST_MODE=False, DEBUG=True):
            response = self._confirm(tx)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        self.booking.refresh_from_db()
        tx.refresh_from_db()
        assert self.booking.status == 'pending'
        assert tx.status == 'processing'

    def test_confirm_forbidden_without_debug(self):
        tx = self._create_transaction(self.booking, 'k-c2')

        with self.settings(PAYMENT_TEST_MODE=True, DEBUG=False):
            response = self._confirm(tx)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        self.booking.refresh_from_db()
        assert self.booking.status == 'pending'

    def test_confirm_works_in_test_mode_with_debug(self):
        tx = self._create_transaction(self.booking, 'k-c3')

        with self.settings(PAYMENT_TEST_MODE=True, DEBUG=True):
            response = self._confirm(tx)

        assert response.status_code == status.HTTP_200_OK
        self.booking.refresh_from_db()
        assert self.booking.status == 'confirmed'

    def test_failed_booking_confirmation_leaves_payment_unchanged(self):
        """If the booking cannot be confirmed, the payment is not marked completed."""
        tx = self._create_transaction(self.booking, 'k-c4')
        Booking.objects.filter(pk=self.booking.pk).update(status='cancelled')

        with self.settings(PAYMENT_TEST_MODE=True, DEBUG=True):
            response = self._confirm(tx)

        assert response.status_code == status.HTTP_409_CONFLICT
        tx.refresh_from_db()
        assert tx.status == 'processing'

    def test_create_returns_503_when_provider_not_integrated(self):
        with self.settings(PAYMENT_TEST_MODE=False):
            response = self.client.post(TRANSACTIONS_URL, self._payment_data(self.booking, 'k-c5'), format='json')

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        tx = PaymentTransaction.objects.get(idempotency_key='k-c5')
        assert tx.status == 'failed'
        assert tx.error_code == 'PROVIDER_UNAVAILABLE'


class TestWebhookSignatureFirst(TestCase):
    """#6: unsigned requests cannot claim real event IDs; secrets fail closed."""

    def setUp(self):
        from payments.webhooks import WebhookProcessor

        self.processor = WebhookProcessor('payme')
        self.payload = {'id': 'evt-real-1', 'transaction_id': 'txn-1', 'status': 'completed',
                        'timestamp': int(timezone.now().timestamp())}

    def _sign(self, payload, secret='test_secret'):
        return self.processor.adapter.generate_signature(payload, secret)

    def test_forged_request_does_not_block_genuine_event(self):
        from payments.adapters import SignatureValidationError
        from payments.models import WebhookEvent

        with mock.patch.object(self.processor.adapter, 'secret_key', 'test_secret'):
            with self.assertRaises(SignatureValidationError):
                self.processor.process_webhook(self.payload, 'forged-signature')

            event, is_new = self.processor.process_webhook(self.payload, self._sign(self.payload))

        assert is_new is True
        assert event.provider_event_id == 'evt-real-1'
        assert event.signature_valid is True
        forged = WebhookEvent.objects.get(status='invalid_signature')
        assert forged.provider_event_id.startswith('invalid_')
        assert forged.signature_valid is False

    def test_replayed_event_is_not_processed_twice(self):
        from payments.models import PaymentAuditLog

        with mock.patch.object(self.processor.adapter, 'secret_key', 'test_secret'):
            self.processor.process_webhook(self.payload, self._sign(self.payload))
            _, is_new = self.processor.process_webhook(self.payload, self._sign(self.payload))

        assert is_new is False
        assert PaymentAuditLog.objects.filter(action='webhook_processed').count() == 1


class TestWebhookSecretFailsClosed(TestCase):
    """Webhooks are always rejected when the provider secret is missing or blank."""

    def setUp(self):
        self.payload = {'id': 'evt-nosecret', 'transaction_id': 'txn-9', 'status': 'completed',
                        'timestamp': int(timezone.now().timestamp())}

    def _assert_rejected(self, provider, secret_setting, secret_value):
        from payments.adapters import get_payment_adapter
        from payments.models import WebhookEvent
        from payments.webhooks import WebhookNotConfiguredError, WebhookProcessor

        with self.settings(**{secret_setting: secret_value}):
            processor = WebhookProcessor(provider)
            # A signature an attacker can compute when the key is empty
            signature = get_payment_adapter(provider).generate_signature(self.payload, secret_value)
            with self.assertRaises(WebhookNotConfiguredError):
                processor.process_webhook(self.payload, signature)

        assert not WebhookEvent.objects.exists()

    def test_payme_empty_secret_rejects(self):
        self._assert_rejected('payme', 'PAYME_SECRET_KEY', '')

    def test_payme_blank_secret_rejects(self):
        self._assert_rejected('payme', 'PAYME_SECRET_KEY', '   ')

    def test_click_empty_secret_rejects(self):
        self._assert_rejected('click', 'CLICK_SECRET_KEY', '')

    def test_visa_empty_secret_rejects(self):
        self._assert_rejected('visa', 'VISA_SECRET_KEY', '')


class TestWebhookAppliesPayment(PaymentSecurityTestBase):
    """#5: signed provider webhooks reach the endpoint without a session and settle payments."""

    SECRET = 'webhook-test-secret'

    def setUp(self):
        super().setUp()
        self.tx = self._create_transaction(self.booking, 'k-wh', provider_transaction_id='txn-wh-1')
        self.provider_client = APIClient()  # no session, like a real provider

    # Payme reports tiyin (R6): 30000 tiyin = 300.00, the transaction amount
    def _post_webhook(self, event_id, provider_status='completed', amount='30000'):
        from payments.adapters import get_payment_adapter

        payload = {'id': event_id, 'transaction_id': 'txn-wh-1', 'status': provider_status,
                   'amount': amount, 'currency': 'USD', 'timestamp': int(timezone.now().timestamp())}
        signature = get_payment_adapter('payme').generate_signature(payload, self.SECRET)
        with self.settings(PAYME_SECRET_KEY=self.SECRET):
            return self.provider_client.post(
                '/api/v1/payments/webhook/payme/', payload, format='json', HTTP_X_SIGNATURE=signature
            )

    def test_unauthenticated_signed_webhook_confirms_booking(self):
        response = self._post_webhook('evt-ok')

        assert response.status_code == status.HTTP_200_OK
        self.tx.refresh_from_db()
        self.booking.refresh_from_db()
        assert self.tx.status == 'completed'
        assert self.booking.status == 'confirmed'
        assert self.booking.payment_status == 'paid'

    def test_amount_mismatch_does_not_confirm(self):
        response = self._post_webhook('evt-cheap', amount='1')

        assert response.status_code == status.HTTP_200_OK
        self.tx.refresh_from_db()
        self.booking.refresh_from_db()
        assert self.tx.status == 'processing'
        assert self.booking.status == 'pending'

    def test_failed_status_marks_transaction_failed(self):
        self._post_webhook('evt-fail', provider_status='failed')

        self.tx.refresh_from_db()
        self.booking.refresh_from_db()
        assert self.tx.status == 'failed'
        assert self.booking.status == 'pending'

    def test_late_failure_cannot_undo_completed_payment(self):
        self._post_webhook('evt-ok-2')
        self._post_webhook('evt-late-fail', provider_status='failed')

        self.tx.refresh_from_db()
        assert self.tx.status == 'completed'

    def test_replayed_webhook_is_acknowledged_without_reprocessing(self):
        from payments.models import PaymentAuditLog

        first = self._post_webhook('evt-dup')
        second = self._post_webhook('evt-dup')

        assert first.status_code == second.status_code == status.HTTP_200_OK
        assert 'already processed' in second.data['message']
        assert PaymentAuditLog.objects.filter(action='payment_completed').count() == 1

    def test_failed_event_is_reprocessed_when_provider_retries(self):
        """A processing error must not turn the provider's retry into a silent no-op."""
        with mock.patch('payments.webhooks.WebhookProcessor._apply_payment_status',
                        side_effect=RuntimeError('db down')):
            failed = self._post_webhook('evt-retry')
        assert failed.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        retry = self._post_webhook('evt-retry')

        assert retry.status_code == status.HTTP_200_OK
        self.tx.refresh_from_db()
        self.booking.refresh_from_db()
        assert self.tx.status == 'completed'
        assert self.booking.status == 'confirmed'

    def test_out_of_range_timestamp_does_not_crash_webhook(self):
        from payments.adapters import get_payment_adapter

        payload = {'id': 'evt-ts', 'transaction_id': 'txn-wh-1', 'status': 'completed',
                   'amount': '30000', 'currency': 'USD', 'timestamp': 1e30}
        signature = get_payment_adapter('payme').generate_signature(payload, self.SECRET)
        with self.settings(PAYME_SECRET_KEY=self.SECRET):
            response = self.provider_client.post(
                '/api/v1/payments/webhook/payme/', payload, format='json', HTTP_X_SIGNATURE=signature
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_webhook_cannot_settle_another_providers_transaction(self):
        from payments.adapters import get_payment_adapter

        payload = {'id': 'evt-cross', 'transaction_id': 'txn-wh-1', 'status': 'completed',
                   'amount': '300.00', 'currency': 'USD', 'timestamp': int(timezone.now().timestamp())}
        signature = get_payment_adapter('click').generate_signature(payload, self.SECRET)
        with self.settings(CLICK_SECRET_KEY=self.SECRET):
            self.provider_client.post(
                '/api/v1/payments/webhook/click/', payload, format='json', HTTP_X_SIGNATURE=signature
            )

        self.tx.refresh_from_db()
        assert self.tx.status == 'processing'

    def test_payment_for_cancelled_booking_is_recorded_and_flagged(self):
        from payments.models import PaymentAuditLog

        Booking.objects.filter(pk=self.booking.pk).update(status='cancelled')

        self._post_webhook('evt-cancelled')

        self.tx.refresh_from_db()
        self.booking.refresh_from_db()
        assert self.tx.status == 'completed'
        assert self.booking.status == 'cancelled'
        log = PaymentAuditLog.objects.get(action='payment_completed')
        assert 'manual refund' in log.details['error']

    def test_forged_webhook_is_rejected(self):
        with self.settings(PAYME_SECRET_KEY=self.SECRET):
            response = self.provider_client.post(
                '/api/v1/payments/webhook/payme/',
                {'id': 'evt-forged', 'transaction_id': 'txn-wh-1', 'status': 'completed', 'amount': '300.00'},
                format='json', HTTP_X_SIGNATURE='forged'
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        self.tx.refresh_from_db()
        assert self.tx.status == 'processing'

    def test_webhook_signature_error_does_not_leak_details(self):
        """audit #24: SignatureValidationError branch must not echo str(e) to the caller."""
        from payments.adapters import SignatureValidationError

        secret = 'internal signature parsing detail: key=sk_live_abcdef'
        with mock.patch('payments.views.get_webhook_processor') as mock_get_processor:
            mock_get_processor.return_value.process_webhook.side_effect = SignatureValidationError(secret)
            response = self.provider_client.post(
                '/api/v1/payments/webhook/payme/', {'id': 'evt-x'}, format='json', HTTP_X_SIGNATURE='sig'
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert secret not in str(response.data)

    def test_webhook_value_error_does_not_leak_details(self):
        """audit #24: ValueError branch must not echo str(e) to the caller."""
        secret = 'internal parsing detail: unexpected token at offset 42'
        with mock.patch('payments.views.get_webhook_processor') as mock_get_processor:
            mock_get_processor.return_value.process_webhook.side_effect = ValueError(secret)
            response = self.provider_client.post(
                '/api/v1/payments/webhook/payme/', {'id': 'evt-y'}, format='json', HTTP_X_SIGNATURE='sig'
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert secret not in str(response.data)

    def test_webhook_unexpected_error_does_not_leak_details(self):
        """audit #24: the generic Exception branch must not echo str(e) to the caller."""
        secret = 'psycopg2.OperationalError: connection to internal-db-host failed'
        with mock.patch('payments.views.get_webhook_processor') as mock_get_processor:
            mock_get_processor.return_value.process_webhook.side_effect = Exception(secret)
            response = self.provider_client.post(
                '/api/v1/payments/webhook/payme/', {'id': 'evt-z'}, format='json', HTTP_X_SIGNATURE='sig'
            )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert secret not in str(response.data)


class TestRefunds(PaymentSecurityTestBase):
    """#15: refunds are staff-only and record the right status."""

    def setUp(self):
        super().setUp()
        Booking.objects.filter(pk=self.booking.pk).update(status='confirmed', payment_status='paid')
        self.tx = self._create_transaction(self.booking, 'k-refund', tx_status='completed')
        self.url = f'{TRANSACTIONS_URL}{self.tx.id}/refund/'

    def _refund_as_staff(self, data=None):
        self.client.force_authenticate(user=self.staff)
        return self.client.post(self.url, data or {}, format='json')

    def test_guest_cannot_refund_own_payment(self):
        response = self.client.post(self.url, {}, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        self.tx.refresh_from_db()
        assert self.tx.status == 'completed'

    def test_full_refund_when_amount_omitted(self):
        response = self._refund_as_staff()

        assert response.status_code == status.HTTP_200_OK
        self.tx.refresh_from_db()
        self.booking.refresh_from_db()
        assert self.tx.status == 'refunded'
        assert self.booking.payment_status == 'refunded'

    def test_full_refund_when_amount_equals_payment(self):
        self._refund_as_staff({'amount': '300.00'})

        self.tx.refresh_from_db()
        assert self.tx.status == 'refunded'

    def test_partial_refund(self):
        response = self._refund_as_staff({'amount': '100.00'})

        assert response.status_code == status.HTTP_200_OK
        self.tx.refresh_from_db()
        self.booking.refresh_from_db()
        assert self.tx.status == 'partially_refunded'
        assert self.booking.payment_status == 'partially_refunded'

    def test_refund_does_not_cancel_booking(self):
        self._refund_as_staff()

        self.booking.refresh_from_db()
        assert self.booking.status == 'confirmed'

    def test_invalid_refund_amounts_are_rejected(self):
        for amount in ('300.01', '0', '-5', 'abc', 'NaN'):
            response = self._refund_as_staff({'amount': amount})
            assert response.status_code == status.HTTP_400_BAD_REQUEST, amount

        self.tx.refresh_from_db()
        assert self.tx.status == 'completed'

    def test_refund_of_payment_for_unpaid_booking_still_recorded(self):
        """Money captured after the booking was cancelled can still be refunded."""
        Booking.objects.filter(pk=self.booking.pk).update(status='cancelled', payment_status='pending')

        response = self._refund_as_staff()

        assert response.status_code == status.HTTP_200_OK
        self.tx.refresh_from_db()
        self.booking.refresh_from_db()
        assert self.tx.status == 'refunded'
        assert self.booking.payment_status == 'pending'


class TestOneActivePaymentPerBooking(PaymentSecurityTestBase):
    """N-5: a double click or a second provider must not create a second charge."""

    def _pay(self, key):
        return self.client.post(TRANSACTIONS_URL, self._payment_data(self.booking, key), format='json')

    def test_second_payment_while_one_is_processing_is_refused(self):
        self._create_transaction(self.booking, 'k-first', tx_status='processing')

        response = self._pay('k-second')

        assert response.status_code == status.HTTP_409_CONFLICT
        assert PaymentTransaction.objects.filter(booking=self.booking).count() == 1

    def test_second_payment_after_a_completed_one_is_refused(self):
        self._create_transaction(self.booking, 'k-done', tx_status='completed')

        assert self._pay('k-again').status_code == status.HTTP_409_CONFLICT

    def test_fresh_pending_payment_blocks_a_double_click(self):
        self._create_transaction(self.booking, 'k-click', tx_status='pending')

        assert self._pay('k-click-2').status_code == status.HTTP_409_CONFLICT

    def test_stale_pending_payment_does_not_block_a_retry(self):
        old = self._create_transaction(self.booking, 'k-old', tx_status='pending')
        PaymentTransaction.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(minutes=30))

        assert self._pay('k-retry').status_code == status.HTTP_201_CREATED

    def test_failed_payment_does_not_block_a_retry(self):
        self._create_transaction(self.booking, 'k-bad', tx_status='failed')

        assert self._pay('k-retry-2').status_code == status.HTTP_201_CREATED

    def test_same_key_still_replays_the_original(self):
        first = self._pay('k-same')
        second = self._pay('k-same')

        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_200_OK
