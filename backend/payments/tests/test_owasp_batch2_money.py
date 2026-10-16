"""
OWASP 2025 batch 2 (A10 exceptional conditions, A04, A06): money paths that failed silently.

Each test names the situation as a guest or staff member would meet it.
"""
from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from payments.adapters import PaymeAdapter
from payments.models import PaymentAuditLog, PaymentTransaction, Refund
from payments.refunds import RefundError, create_refund, retry_refund, send_refund
from payments.tests.test_r12_refunds import _client, _paid_booking, people  # noqa: F401  (fixture)

TX_URL = '/api/v1/payments/transactions/'


@pytest.fixture
def paid(people):  # noqa: F811
    booking, tx = _paid_booking(people)
    return {'booking': booking, 'tx': tx}


@pytest.mark.django_db
class TestRefundNeverGetsStuck:
    def test_an_unexpected_provider_error_marks_the_refund_failed_not_pending(self, paid):
        refund = create_refund(paid['tx'], paid['tx'].amount, 'staff')

        with mock.patch.object(PaymeAdapter, 'refund_payment', side_effect=TimeoutError('provider timed out')):
            result = send_refund(refund)

        assert (result.status, result.error_code) == ('failed', 'REFUND_ERROR')

    def test_a_refund_pending_for_over_an_hour_can_be_retried(self, paid, people):
        refund = create_refund(paid['tx'], paid['tx'].amount, 'staff')
        Refund.objects.filter(pk=refund.pk).update(created_at=timezone.now() - timedelta(hours=2))

        with mock.patch.object(PaymeAdapter, 'refund_payment', return_value={'refund_id': 'r-1'}):
            result = retry_refund(Refund.objects.get(pk=refund.pk), people['super'])

        assert result.status == 'succeeded'

    def test_a_fresh_pending_refund_cannot_be_retried_it_may_still_be_in_flight(self, paid, people):
        refund = create_refund(paid['tx'], paid['tx'].amount, 'staff')

        with pytest.raises(RefundError) as error:
            retry_refund(refund, people['super'])

        assert error.value.code == 'not_failed'
        assert Refund.objects.get(pk=refund.pk).status == 'pending'


@pytest.mark.django_db
class TestPaymentCreateKeepsTheRecordTruthful:
    def _pay(self, people, booking, key='create-1'):
        client = _client(people['guest'])
        return client.post(TX_URL, {
            'idempotency_key': key, 'booking': booking.id, 'provider': 'payme',
            'amount': str(booking.charge_amount), 'currency': booking.charge_currency,
        }, format='json')

    def test_an_unexpected_provider_error_fails_the_transaction_and_answers_502(self, people):
        from payments.tests.test_r12_refunds import _paid_booking as make
        booking, tx = make(people, key='seed')
        PaymentTransaction.objects.filter(pk=tx.pk).delete()
        type(booking).objects.filter(pk=booking.pk).update(status='pending', payment_status='pending',
                                                           expires_at=timezone.now() + timedelta(minutes=10))

        with mock.patch.object(PaymeAdapter, 'initiate_payment', side_effect=ConnectionError('boom')):
            response = self._pay(people, booking)

        assert response.status_code == 502
        created = PaymentTransaction.objects.get(idempotency_key='create-1')
        assert (created.status, created.error_code) == ('failed', 'PROVIDER_ERROR')
        assert 'boom' not in str(response.data)


from django.test import override_settings  # noqa: E402

from bookings.models import Booking  # noqa: E402
from payments.models import WebhookEvent  # noqa: E402
from bookings.tests.test_quote import stay  # noqa: E402,F401  (fixture used by `booked`)
from payments.tests.test_r6_payments import CHARGE, SECRET, _pay, booked  # noqa: E402,F401  (fixture)


def _send_webhook(event_id, provider_transaction_id='txn-1', status='completed', amount=int(CHARGE) * 100):
    payload = {'id': event_id, 'transaction_id': provider_transaction_id, 'status': status, 'amount': amount,
               'currency': 'UZS', 'timestamp': int(timezone.now().timestamp())}
    signature = PaymeAdapter().generate_signature(payload, SECRET)
    with override_settings(PAYME_SECRET_KEY=SECRET):
        return APIClient().post('/api/v1/payments/webhook/payme/', payload, format='json', HTTP_X_SIGNATURE=signature)


@pytest.mark.django_db
class TestPaidWebhookIsNeverSilentlyDropped:
    """A10-2: a validly signed 'paid' message that cannot be applied must be retried, not acknowledged."""

    def _processing_tx(self, booked):
        assert _pay(booked, 'k-1').status_code == 201
        tx = PaymentTransaction.objects.get(idempotency_key='k-1')
        PaymentTransaction.objects.filter(pk=tx.pk).update(provider_transaction_id='txn-1')
        return tx

    def test_a_payment_the_provider_reports_before_we_know_it_is_retried_later(self, booked):
        tx = self._processing_tx(booked)
        PaymentTransaction.objects.filter(pk=tx.pk).update(provider_transaction_id=None)  # webhook raced the save

        first = _send_webhook('evt-early')

        assert first.status_code == 409
        event = WebhookEvent.objects.get(provider_event_id='evt-early')
        assert event.status == 'failed'
        assert PaymentAuditLog.objects.filter(webhook_event=event).exists()

        PaymentTransaction.objects.filter(pk=tx.pk).update(provider_transaction_id='txn-1')
        retry = _send_webhook('evt-early')

        assert retry.status_code == 200
        tx.refresh_from_db()
        assert tx.status == 'completed'
        assert Booking.objects.get(pk=tx.booking_id).status == 'confirmed'

    def test_a_wrong_amount_is_recorded_as_failed_and_applies_nothing(self, booked):
        tx = self._processing_tx(booked)

        response = _send_webhook('evt-wrong', amount=int(CHARGE) * 100 + 1)

        assert response.status_code == 409
        assert WebhookEvent.objects.get(provider_event_id='evt-wrong').status == 'failed'
        tx.refresh_from_db()
        assert tx.status in ('pending', 'processing')
        assert Booking.objects.get(pk=tx.booking_id).status == 'pending'

    def test_an_informational_event_for_an_unknown_transaction_is_still_acknowledged(self, booked):
        response = _send_webhook('evt-ping', provider_transaction_id='unknown', status='created')

        assert response.status_code == 200
        assert WebhookEvent.objects.get(provider_event_id='evt-ping').status == 'processed'

    def test_a_replay_of_an_applied_event_is_acknowledged_without_changing_anything(self, booked):
        tx = self._processing_tx(booked)
        assert _send_webhook('evt-ok').status_code == 200

        again = _send_webhook('evt-ok')

        assert again.status_code == 200
        tx.refresh_from_db()
        assert tx.status == 'completed'


@pytest.mark.django_db
class TestPaymentInFlightHoldsTheBooking:
    """A10-3: paying at minute 14 and the webhook arriving at minute 16 must not lose the room."""

    def _expired_pending_with_payment(self, booked, payment_age=timedelta(minutes=1)):
        assert _pay(booked, 'k-fly').status_code == 201
        tx = PaymentTransaction.objects.get(idempotency_key='k-fly')
        PaymentTransaction.objects.filter(pk=tx.pk).update(
            provider_transaction_id='txn-fly', status='processing', updated_at=timezone.now() - payment_age)
        Booking.objects.filter(pk=tx.booking_id).update(expires_at=timezone.now() - timedelta(minutes=1))
        return tx

    def test_a_booking_with_a_fresh_payment_in_progress_is_not_expired(self, booked):
        tx = self._expired_pending_with_payment(booked)

        Booking.process_expired_bookings()

        assert Booking.objects.get(pk=tx.booking_id).status == 'pending'

    def test_the_late_webhook_then_confirms_it(self, booked):
        tx = self._expired_pending_with_payment(booked)
        Booking.process_expired_bookings()

        assert _send_webhook('evt-late', provider_transaction_id='txn-fly').status_code == 200

        assert Booking.objects.get(pk=tx.booking_id).status == 'confirmed'

    def test_a_payment_stuck_for_hours_does_not_hold_the_room_for_ever(self, booked):
        tx = self._expired_pending_with_payment(booked, payment_age=timedelta(hours=3))

        Booking.process_expired_bookings()

        assert Booking.objects.get(pk=tx.booking_id).status == 'cancelled'

    def test_an_unpaid_expired_booking_still_expires(self, booked):
        Booking.objects.filter(pk=booked['booking'].pk).update(expires_at=timezone.now() - timedelta(minutes=1))

        Booking.process_expired_bookings()

        assert Booking.objects.get(pk=booked['booking'].pk).status == 'cancelled'


@pytest.mark.django_db
class TestCapturedMoneyForACancelledBookingIsFlaggedForRefund:
    """A10-3: the provider took the money but the booking is gone: staff must see a refund to pay back."""

    def test_a_manual_refund_row_is_created_once(self, booked, people):  # noqa: F811
        assert _pay(booked, 'k-gone').status_code == 201
        tx = PaymentTransaction.objects.get(idempotency_key='k-gone')
        PaymentTransaction.objects.filter(pk=tx.pk).update(provider_transaction_id='txn-gone', status='processing')
        Booking.objects.filter(pk=tx.booking_id).update(status='cancelled')

        assert _send_webhook('evt-gone', provider_transaction_id='txn-gone').status_code == 200
        assert _send_webhook('evt-gone', provider_transaction_id='txn-gone').status_code == 200

        tx.refresh_from_db()
        assert tx.status == 'completed'
        refunds = Refund.objects.filter(payment=tx)
        assert [(r.status, r.amount, r.error_code) for r in refunds] == [
            ('needs_manual', tx.amount, 'BOOKING_NOT_CONFIRMABLE')]
        staff = people['staff']
        listing = _client(staff).get('/api/v1/admin-panel/refunds/needs-attention/')
        assert [row['id'] for row in listing.data['results']] == [refunds[0].id]


@pytest.mark.django_db
class TestAuditFailuresAreNotSwallowed:
    """A10-5: a failed history write is logged and cannot poison the surrounding transaction."""

    def _database_error(self, *args, **kwargs):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1/0')

    @pytest.mark.parametrize('method, arguments', [
        ('_log_state_transition', ('pending', 'confirmed', 'test')),
        ('_log_payment_status_transition', ('pending', 'paid')),
    ])
    def test_a_database_error_in_the_history_write_is_logged_and_the_transaction_survives(
            self, paid, caplog, method, arguments):
        from django.db import transaction

        booking = paid['booking']
        with mock.patch.object(PaymentAuditLog, 'log_action', side_effect=self._database_error):
            with transaction.atomic():
                getattr(booking, method)(*arguments)
                survived = Booking.objects.filter(pk=booking.pk).exists()  # fails on an aborted transaction

        assert survived
        assert [r for r in caplog.records if r.levelname == 'ERROR' and r.exc_info]


@pytest.mark.django_db
class TestCardNumberIsNeverAcceptedAsAToken:
    """A04-1: the token field is free text; a pasted card number must not reach the database."""

    @pytest.mark.parametrize('token', [
        '4242424242424242', '4242 4242 4242 4242', '4242-4242-4242-4242', 'tok_4242424242424242',
        '9860123456789012', '378282246310005',
    ])
    def test_a_card_number_is_refused_and_nothing_is_stored(self, booked, token):
        response = _pay(booked, 'k-pan', payment_method_token=token)

        assert response.status_code == 400
        assert not PaymentTransaction.objects.exists()
        assert token.replace(' ', '') not in str(response.data)

    @pytest.mark.parametrize('token', ['tok_abc123XYZ', 'f47ac10b-58cc-4372-a567-0e02b2c3d479', 'pm_1'])
    def test_an_ordinary_provider_token_is_accepted(self, booked, token):
        response = _pay(booked, 'k-token', payment_method_token=token)

        assert response.status_code == 201, response.data


@pytest.mark.django_db
class TestDatabaseOutageIsNotAClientError:
    """A10-9: a database error while booking, cancelling or using an OTP is a 5xx, not 'please try again' (400)."""

    def _fail(self):
        from django.db import OperationalError
        return OperationalError('database is down')

    def test_booking_create(self, booked):
        body = {'property_id': booked['property'].id, 'room_type_id': booked['room'].id,
                'rate_plan_id': booked['rate'].id,
                'check_in': (booked['start'] + timedelta(days=6)).isoformat(),
                'check_out': (booked['start'] + timedelta(days=7)).isoformat(), 'guest_count': 1}
        client = booked['client']
        client.raise_request_exception = False

        with mock.patch.object(Booking, 'create_booking', side_effect=self._fail()):
            response = client.post('/api/v1/bookings/', body, format='json')

        assert response.status_code == 500

    def test_booking_cancel(self, booked):
        client = booked['client']
        client.raise_request_exception = False

        with mock.patch.object(Booking, 'cancel_booking', side_effect=self._fail()):
            response = client.post(f"/api/v1/bookings/{booked['booking'].id}/cancel/", {}, format='json')

        assert response.status_code == 500

@pytest.mark.django_db
class TestPaidStayCannotBeCancelledOnceItHasStarted:
    """A06-4: cancelling on or after check-in day would keep the room, free the inventory and strand the money."""

    def _cancel(self, booked, status, check_in_offset):
        from common.dates import business_today
        today = business_today()
        Booking.objects.filter(pk=booked['booking'].pk).update(
            status=status, check_in=today + timedelta(days=check_in_offset),
            check_out=today + timedelta(days=check_in_offset + 2))
        return booked['client'].post(f"/api/v1/bookings/{booked['booking'].id}/cancel/", {}, format='json')

    @pytest.mark.parametrize('offset', [0, -1])
    def test_a_confirmed_booking_cannot_be_cancelled_from_check_in_day(self, booked, offset):
        response = self._cancel(booked, 'confirmed', offset)

        assert response.status_code == 400
        assert Booking.objects.get(pk=booked['booking'].pk).status == 'confirmed'

    def test_a_confirmed_booking_can_be_cancelled_before_check_in(self, booked):
        assert self._cancel(booked, 'confirmed', 1).status_code == 200

    def test_an_unpaid_booking_can_always_be_cancelled(self, booked):
        assert self._cancel(booked, 'pending', 0).status_code == 200
