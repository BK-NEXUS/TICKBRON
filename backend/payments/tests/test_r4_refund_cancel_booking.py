"""
R4 / fix plan #6: POST /payments/transactions/{id}/refund/ with optional cancel_booking.

cancel_booking=true refunds and cancels in one transaction: the booking is
cancelled, its rooms go back to inventory, the payment and booking payment status
change, and both steps are in the audit log. If the booking cannot be cancelled,
nothing is refunded. Without the flag the booking is untouched (existing behaviour).
"""
from datetime import timedelta
from unittest import mock

import pytest
from django.db import DatabaseError
from rest_framework.test import APIClient

from bookings.models import Booking
from bookings.tests.test_quote import stay  # noqa: F401  (fixture)
from payments.adapters import PaymeAdapter
from payments.models import PaymentAuditLog, PaymentTransaction
from properties.models import RoomInventory
from users.models import User
from currency.testing import make_usd_rate

TRANSACTIONS_URL = '/api/v1/payments/transactions/'


@pytest.fixture
def paid(stay):
    """A confirmed, paid two-night booking of 2 rooms and its completed payment."""
    make_usd_rate()  # R6: a USD hotel is bookable only once a rate exists
    booking = Booking.create_booking(
        guest=stay['guest'], property_obj=stay['property'], room_type=stay['room'],
        rate_plan=stay['rate'], check_in=stay['start'], check_out=stay['start'] + timedelta(days=2),
        guest_count=2, number_of_rooms=2,
    )
    Booking.objects.filter(pk=booking.pk).update(status='confirmed', payment_status='paid')
    tx = PaymentTransaction.objects.create(
        idempotency_key='k-refund-cancel', booking=booking, provider='payme',
        amount=booking.charge_amount, currency=booking.charge_currency, status='completed',  # R6: paid in UZS
        provider_transaction_id='txn-refund-cancel',
    )
    staff = User.objects.create_user(email='staff@example.com', password='x', is_staff=True)
    client = APIClient()
    client.force_authenticate(user=staff)
    return {'booking': booking, 'tx': tx, 'client': client, 'stay': stay}


def _booked_rooms(paid):
    return sorted(RoomInventory.objects.filter(room_type=paid['stay']['room'])
                  .values_list('date', 'booked_rooms'))


def _refund(paid, data):
    return paid['client'].post(f"{TRANSACTIONS_URL}{paid['tx'].id}/refund/", data, format='json')


@pytest.mark.django_db
class TestRefundWithCancelBooking:

    def test_full_refund_and_cancel(self, paid):
        assert [rooms for _, rooms in _booked_rooms(paid)] == [2, 2]

        response = _refund(paid, {'cancel_booking': True, 'cancellation_reason': 'Hotel overbooked'})

        assert response.status_code == 200, response.data
        assert response.data['status'] == 'refunded'
        assert response.data['booking_status'] == 'cancelled'
        paid['tx'].refresh_from_db()
        paid['booking'].refresh_from_db()
        assert paid['tx'].status == 'refunded'
        assert paid['booking'].status == 'cancelled'
        assert paid['booking'].payment_status == 'refunded'
        assert paid['booking'].cancellation_reason == 'Hotel overbooked'
        assert [rooms for _, rooms in _booked_rooms(paid)] == [0, 0]

    def test_audit_log_records_refund_and_cancellation(self, paid):
        _refund(paid, {'cancel_booking': True})

        refund_log = PaymentAuditLog.objects.get(action='payment_refunded', payment_transaction=paid['tx'])
        assert refund_log.details['cancel_booking'] is True
        assert refund_log.actor.email == 'staff@example.com'
        assert PaymentAuditLog.objects.filter(
            action='booking_status_changed', booking=paid['booking'], new_status='cancelled'
        ).exists()

    def test_partial_refund_and_cancel(self, paid):
        response = _refund(paid, {'amount': '10.00', 'cancel_booking': True})

        assert response.status_code == 200, response.data
        paid['booking'].refresh_from_db()
        assert paid['booking'].status == 'cancelled'
        assert paid['booking'].payment_status == 'partially_refunded'

    def test_without_flag_booking_and_rooms_are_untouched(self, paid):
        response = _refund(paid, {})

        assert response.status_code == 200
        assert response.data['booking_status'] == 'confirmed'
        paid['booking'].refresh_from_db()
        assert paid['booking'].status == 'confirmed'
        assert [rooms for _, rooms in _booked_rooms(paid)] == [2, 2]

    def test_booking_that_cannot_be_cancelled_is_not_refunded(self, paid):
        Booking.objects.filter(pk=paid['booking'].pk).update(status='completed')

        with mock.patch.object(PaymeAdapter, 'refund_payment') as provider_refund:
            response = _refund(paid, {'cancel_booking': True})

        assert response.status_code == 400
        provider_refund.assert_not_called()
        paid['tx'].refresh_from_db()
        assert paid['tx'].status == 'completed'

    def test_invalid_flag_is_rejected(self, paid):
        response = _refund(paid, {'cancel_booking': 'maybe'})

        assert response.status_code == 400
        paid['tx'].refresh_from_db()
        assert paid['tx'].status == 'completed'

    def test_failure_while_cancelling_rolls_everything_back(self, paid):
        with mock.patch.object(Booking, 'cancel_booking', side_effect=DatabaseError('boom')):
            client = paid['client']
            client.raise_request_exception = False
            response = _refund(paid, {'cancel_booking': True})

        assert response.status_code == 500
        paid['tx'].refresh_from_db()
        paid['booking'].refresh_from_db()
        assert paid['tx'].status == 'completed'
        assert paid['booking'].payment_status == 'paid'
        assert paid['booking'].status == 'confirmed'
        assert [rooms for _, rooms in _booked_rooms(paid)] == [2, 2]

    def test_second_refund_is_rejected(self, paid):
        assert _refund(paid, {'cancel_booking': True}).status_code == 200

        response = _refund(paid, {'cancel_booking': True})

        assert response.status_code == 400

    def test_guest_cannot_refund_and_cancel(self, paid):
        client = APIClient()
        client.force_authenticate(user=paid['booking'].guest)

        response = client.post(f"{TRANSACTIONS_URL}{paid['tx'].id}/refund/", {'cancel_booking': True}, format='json')

        assert response.status_code == 403
        paid['booking'].refresh_from_db()
        assert paid['booking'].status == 'confirmed'
