"""
R12 1c: every refund is a Refund row (payment, booking, amount, reason, status,
idempotency key, provider reference, error code, created_by).

- The sum of non-failed refunds of a payment never exceeds the payment amount,
  checked in a transaction with the payment row locked.
- The provider is called only after the refund row is committed.
- Adapters declare whether partial refunds are supported; where unsupported or
  unverified the provider is not called and the refund is `needs_manual`.
- The staff refund endpoint keeps its API shape and writes through the model.
"""
import threading
from datetime import timedelta
from decimal import Decimal
from unittest import mock

import pytest
from django.db import connection, transaction
from django.test import override_settings
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from bookings.models import Booking
from bookings.state_machine import BookingState, BookingStateMachine
from bookings.tests.r12_helpers import make_booking
from common.dates import business_today
from payments.adapters import ClickAdapter, PaymeAdapter, PaymentAdapterError, VisaAdapter, get_payment_adapter
from payments.models import PaymentTransaction, Refund
from payments.refunds import RefundError, create_refund, remaining_amount, send_refund
from properties.models import Property, PropertyType
from users.models import User

TX_URL = '/api/v1/payments/transactions/'
ATTENTION_URL = '/api/v1/admin-panel/refunds/needs-attention/'
PAID = Decimal('1000000')


@pytest.fixture
def people(db):
    return {
        'guest': User.objects.create_user(email='g@example.com', password='x'),
        'owner': User.objects.create_user(email='o@example.com', password='x'),
        'staff': User.objects.create_user(email='s@example.com', password='x', is_staff=True),
        'super': User.objects.create_user(email='a@example.com', password='x', is_staff=True, is_superuser=True),
    }


def _paid_booking(people, provider='payme', key='k1'):
    hotel = Property.objects.create(
        owner=people['owner'], property_type=PropertyType.objects.get_or_create(name='Hotel', slug='hotel')[0],
        status='active', max_guests=2, bedrooms=1, bathrooms=1, address_line1='1 Main',
        city='Tashkent', country='Uzbekistan', base_price=500000, currency='UZS',
    )
    booking = make_booking(hotel, people['guest'], business_today() + timedelta(days=10), nights=2,
                           price=Decimal('500000'))
    tx = PaymentTransaction.objects.create(
        idempotency_key=key, booking=booking, provider=provider, amount=booking.charge_amount,
        currency=booking.charge_currency, status='completed', provider_transaction_id=f'ptx-{key}',
    )
    return booking, tx


@pytest.fixture
def paid(people):
    booking, tx = _paid_booking(people)
    assert tx.amount == PAID
    return {'booking': booking, 'tx': tx}


def _client(user):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestRefundService:

    def test_full_refund_succeeds_and_updates_payment_and_booking(self, paid, people):
        refund = create_refund(paid['tx'], PAID, 'staff', created_by=people['staff'])
        assert refund.status == 'pending'
        assert (refund.payment_id, refund.booking_id, refund.currency) == (paid['tx'].id, paid['booking'].id, 'UZS')

        send_refund(refund)

        refund.refresh_from_db()
        paid['tx'].refresh_from_db()
        paid['booking'].refresh_from_db()
        assert refund.status == 'succeeded'
        assert refund.provider_reference
        assert paid['tx'].status == 'refunded'
        assert paid['booking'].payment_status == 'refunded'

    def test_partial_refunds_add_up_and_never_exceed_the_payment(self, paid):
        first = send_refund(create_refund(paid['tx'], Decimal('600000'), 'staff'))
        assert first.status == 'succeeded'
        paid['tx'].refresh_from_db()
        assert paid['tx'].status == 'partially_refunded'
        assert remaining_amount(paid['tx']) == Decimal('400000')

        with pytest.raises(RefundError) as error:
            create_refund(paid['tx'], Decimal('400001'), 'staff')
        assert error.value.code == 'limit_exceeded'
        assert Refund.objects.count() == 1

        send_refund(create_refund(paid['tx'], Decimal('400000'), 'staff'))
        paid['tx'].refresh_from_db()
        assert paid['tx'].status == 'refunded'

    def test_pending_and_needs_manual_refunds_count_against_the_limit(self, paid):
        create_refund(paid['tx'], Decimal('700000'), 'staff')   # pending, not sent
        with pytest.raises(RefundError):
            create_refund(paid['tx'], Decimal('300001'), 'staff')

    def test_failed_refund_does_not_count(self, paid):
        with mock.patch.object(PaymeAdapter, 'refund_payment', side_effect=PaymentAdapterError('down')):
            failed = send_refund(create_refund(paid['tx'], PAID, 'staff'))
        assert failed.status == 'failed'
        assert failed.error_code == 'REFUND_ERROR'
        paid['tx'].refresh_from_db()
        assert paid['tx'].status == 'completed'
        assert remaining_amount(paid['tx']) == PAID
        assert send_refund(create_refund(paid['tx'], PAID, 'staff')).status == 'succeeded'

    @pytest.mark.parametrize('amount', [Decimal('0'), Decimal('-5'), Decimal('100.50')])
    def test_invalid_amounts(self, paid, amount):
        with pytest.raises(RefundError):
            create_refund(paid['tx'], amount, 'staff')
        assert not Refund.objects.exists()

    def test_unpaid_payment_cannot_be_refunded(self, paid):
        PaymentTransaction.objects.filter(pk=paid['tx'].pk).update(status='pending')
        paid['tx'].refresh_from_db()
        with pytest.raises(RefundError) as error:
            create_refund(paid['tx'], PAID, 'staff')
        assert error.value.code == 'payment_not_refundable'

    def test_same_idempotency_key_returns_the_same_refund(self, paid):
        first = create_refund(paid['tx'], Decimal('500000'), 'no_show', idempotency_key='b1:no_show')
        again = create_refund(paid['tx'], Decimal('500000'), 'no_show', idempotency_key='b1:no_show')
        assert first.pk == again.pk
        assert Refund.objects.count() == 1

    def test_sending_twice_calls_the_provider_once(self, paid):
        refund = create_refund(paid['tx'], PAID, 'staff')
        with mock.patch.object(PaymeAdapter, 'refund_payment', return_value={'success': True}) as provider:
            send_refund(refund)
            send_refund(Refund.objects.get(pk=refund.pk))
        assert provider.call_count == 1

    @override_settings(PAYMENT_TEST_MODE=False)
    def test_partial_refund_with_unverified_provider_needs_manual_and_skips_the_provider(self, paid):
        with mock.patch.object(PaymeAdapter, 'refund_payment') as provider:
            refund = send_refund(create_refund(paid['tx'], Decimal('500000'), 'staff'))
        provider.assert_not_called()
        assert refund.status == 'needs_manual'
        paid['tx'].refresh_from_db()
        assert paid['tx'].status == 'completed'

    @override_settings(PAYMENT_TEST_MODE=False)
    def test_full_refund_with_production_adapter_calls_the_provider(self, paid):
        with mock.patch.object(PaymeAdapter, 'refund_payment', return_value={'success': True, 'id': 'r-1'}) as p:
            refund = send_refund(create_refund(paid['tx'], PAID, 'staff'))
        p.assert_called_once()
        assert refund.status == 'succeeded'

    def test_refund_row_cannot_be_deleted(self, paid):
        refund = create_refund(paid['tx'], PAID, 'staff')
        with pytest.raises(PermissionError):
            refund.delete()


class TestAdapterDeclarations:

    @pytest.mark.parametrize('adapter', [PaymeAdapter, ClickAdapter, VisaAdapter])
    def test_production_partial_refund_support_is_declared_and_unverified(self, adapter):
        # None = not verified in the provider's documentation/sandbox (RELEASE_CHECKLIST)
        assert adapter.SUPPORTS_PARTIAL_REFUND is None

    @override_settings(PAYMENT_TEST_MODE=False)
    def test_production_adapter_does_not_claim_partial_refunds(self):
        assert get_payment_adapter('payme').partial_refund_supported() is False

    @override_settings(PAYMENT_TEST_MODE=True)
    def test_test_mode_mock_supports_partial_refunds(self):
        assert get_payment_adapter('payme').partial_refund_supported() is True


@pytest.mark.django_db(transaction=True)
class TestLockingAndCommit:

    def test_provider_is_called_outside_any_transaction(self, paid, people):
        seen = {}

        def provider(*args, **kwargs):
            seen['in_atomic'] = connection.in_atomic_block
            seen['committed'] = Refund.objects.filter(status='pending').exists()
            return {'success': True}

        with mock.patch.object(PaymeAdapter, 'refund_payment', side_effect=provider):
            response = _client(people['staff']).post(f"{TX_URL}{paid['tx'].id}/refund/", {}, format='json')
        assert response.status_code == 200, response.data
        assert seen == {'in_atomic': False, 'committed': True}

    def test_concurrent_refunds_cannot_exceed_the_payment(self, paid):
        barrier = threading.Barrier(2)
        results = []

        def worker():
            try:
                barrier.wait()
                with transaction.atomic():
                    create_refund(PaymentTransaction.objects.get(pk=paid['tx'].pk), Decimal('600000'), 'staff')
                results.append('ok')
            except RefundError as error:
                results.append(error.code)
            finally:
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert sorted(results) == ['limit_exceeded', 'ok']
        assert Refund.objects.count() == 1


@pytest.mark.django_db
class TestRefundEndpointUsesTheModel:

    def _refund(self, paid, user, data):
        return _client(user).post(f"{TX_URL}{paid['tx'].id}/refund/", data, format='json')

    def test_full_refund_writes_a_refund_row(self, paid, people):
        response = self._refund(paid, people['staff'], {})
        assert response.status_code == 200
        assert response.data['status'] == 'refunded'
        refund = Refund.objects.get()
        assert (refund.amount, refund.reason, refund.status) == (PAID, 'staff', 'succeeded')
        assert refund.created_by == people['staff']
        assert response.data['refund'] == {'id': refund.id, 'amount': '1000000.00', 'currency': 'UZS',
                                           'reason': 'staff', 'status': 'succeeded'}

    def test_refund_with_cancel_has_reason_cancel(self, paid, people):
        response = self._refund(paid, people['staff'], {'cancel_booking': True})
        assert response.status_code == 200
        assert response.data['booking_status'] == 'cancelled'
        assert Refund.objects.get().reason == 'cancel'

    def test_provider_failure_records_a_failed_refund(self, paid, people):
        with mock.patch.object(PaymeAdapter, 'refund_payment', side_effect=PaymentAdapterError('secret')):
            response = self._refund(paid, people['staff'], {})
        assert response.status_code == 400
        assert 'secret' not in str(response.data)
        refund = Refund.objects.get()
        assert (refund.status, refund.error_code) == ('failed', 'REFUND_ERROR')
        paid['tx'].refresh_from_db()
        assert paid['tx'].status == 'completed'

    @override_settings(PAYMENT_TEST_MODE=False)
    def test_partial_refund_with_unverified_provider_is_accepted_for_manual_handling(self, paid, people):
        with mock.patch.object(PaymeAdapter, 'refund_payment') as provider:
            response = self._refund(paid, people['staff'], {'amount': '400000'})
        provider.assert_not_called()
        assert response.status_code == 202
        assert response.data['status'] == 'completed'
        assert response.data['refund']['status'] == 'needs_manual'


@pytest.mark.django_db
class TestNeedsAttention:

    def test_lists_failed_needs_manual_and_old_pending(self, paid, people):
        booking2, tx2 = _paid_booking(people, key='k2')
        booking3, tx3 = _paid_booking(people, key='k3')
        booking4, tx4 = _paid_booking(people, key='k4')
        with mock.patch.object(PaymeAdapter, 'refund_payment', side_effect=PaymentAdapterError('x')):
            failed = send_refund(create_refund(paid['tx'], PAID, 'staff'))
        with override_settings(PAYMENT_TEST_MODE=False):
            manual = send_refund(create_refund(tx2, Decimal('100000'), 'staff'))
        old_pending = create_refund(tx3, PAID, 'staff')
        Refund.objects.filter(pk=old_pending.pk).update(created_at=old_pending.created_at - timedelta(hours=2))
        create_refund(tx4, PAID, 'staff')   # fresh pending: not listed

        response = _client(people['staff']).get(ATTENTION_URL)

        assert response.status_code == 200
        ids = {row['id'] for row in response.data['results']}
        assert ids == {failed.id, manual.id, old_pending.id}
        row = next(r for r in response.data['results'] if r['id'] == failed.id)
        assert row['booking_reference'] == paid['booking'].confirmation_code
        assert row['error_code'] == 'REFUND_ERROR'
        assert 'guest_email' not in row and 'guest_phone' not in row

    @pytest.mark.parametrize('who', [None, 'guest', 'owner'])
    def test_only_staff(self, people, who):
        assert _client(people[who] if who else None).get(ATTENTION_URL).status_code in (401, 403)

    @override_settings(PAYMENT_TEST_MODE=False)
    def test_super_admin_marks_a_manual_refund_done(self, paid, people):
        refund = send_refund(create_refund(paid['tx'], Decimal('400000'), 'staff'))
        url = f'/api/v1/admin-panel/refunds/{refund.id}/mark-done/'

        assert _client(people['staff']).post(url, {'provider_reference': 'bank-1'}, format='json').status_code == 403
        assert _client(people['super']).post(url, {}, format='json').status_code == 400
        response = _client(people['super']).post(url, {'provider_reference': 'bank-1'}, format='json')

        assert response.status_code == 200
        refund.refresh_from_db()
        paid['tx'].refresh_from_db()
        assert (refund.status, refund.provider_reference) == ('succeeded', 'bank-1')
        assert paid['tx'].status == 'partially_refunded'
        log = AdminAccessLog.objects.get(action='refund_mark_done')
        assert (log.actor_id, log.target_booking_id, log.details) == (
            people['super'].id, paid['booking'].id, {'refund_id': refund.id})

    def test_super_admin_retries_a_failed_refund(self, paid, people):
        with mock.patch.object(PaymeAdapter, 'refund_payment', side_effect=PaymentAdapterError('x')):
            refund = send_refund(create_refund(paid['tx'], PAID, 'staff'))
        url = f'/api/v1/admin-panel/refunds/{refund.id}/retry/'

        assert _client(people['staff']).post(url).status_code == 403
        response = _client(people['super']).post(url)

        assert response.status_code == 200, response.data
        refund.refresh_from_db()
        assert refund.status == 'succeeded'
        assert AdminAccessLog.objects.filter(action='refund_retry', target_booking_id=paid['booking'].id).exists()

    def test_retry_refuses_a_refund_that_did_not_fail(self, paid, people):
        refund = send_refund(create_refund(paid['tx'], PAID, 'staff'))
        response = _client(people['super']).post(f'/api/v1/admin-panel/refunds/{refund.id}/retry/')
        assert response.status_code == 400


class TestNoShowAfterCompletion:
    """completed -> no_show exists only for an approved no-show report (phase 3)."""

    def test_refused_without_the_report_reason(self):
        valid, _ = BookingStateMachine.validate_transition(BookingState.COMPLETED, BookingState.NO_SHOW)
        assert not valid
        valid, _ = BookingStateMachine.validate_transition(BookingState.COMPLETED, BookingState.NO_SHOW,
                                                           reason='guest_no_show')
        assert not valid
        assert not BookingStateMachine.can_transition(BookingState.COMPLETED, BookingState.NO_SHOW)

    def test_allowed_with_an_approved_report(self):
        valid, error = BookingStateMachine.validate_transition(BookingState.COMPLETED, BookingState.NO_SHOW,
                                                               reason='no_show_report_approved')
        assert valid, error

    def test_other_terminal_states_stay_terminal(self):
        for target in (BookingState.CONFIRMED, BookingState.CANCELLED, BookingState.PENDING):
            valid, _ = BookingStateMachine.validate_transition(BookingState.COMPLETED, target,
                                                               reason='no_show_report_approved')
            assert not valid

    @pytest.mark.django_db
    def test_mark_no_show_of_a_completed_booking_needs_the_report_flag(self, people):
        hotel = Property.objects.create(
            owner=people['owner'], property_type=PropertyType.objects.create(name='H', slug='h'),
            status='active', max_guests=2, bedrooms=1, bathrooms=1, address_line1='1', city='Tashkent',
            country='Uzbekistan', base_price=1, currency='UZS',
        )
        booking = make_booking(hotel, people['guest'], business_today() - timedelta(days=5), status='completed')
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            booking.mark_no_show()
        booking.mark_no_show(via_approved_report=True)
        assert Booking.objects.get(pk=booking.pk).status == 'no_show'
