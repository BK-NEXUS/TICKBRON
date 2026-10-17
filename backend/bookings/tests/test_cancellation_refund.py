"""
R11: a guest cancels a paid booking and gets back what the rate plan promised when they booked
(.ai/PLAN_R11_CANCELLATION.md). The percent is decided on the backend from the snapshot on the booking.

POST /bookings/{id}/cancel/          cancels and refunds in one transaction (guest only)
GET  /bookings/{id}/cancel-preview/  what a cancel right now would give back
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from bookings.models import Booking
from bookings.tests.r12b_helpers import client_for, make_stay, pay, world  # noqa: F401
from payments.models import Refund

BASE = '/api/v1/bookings'
CHARGE = Decimal('2354590')          # 2 nights x 1 177 295


def stay(world, free_in=None, percent=50, **kwargs):
    """A confirmed, paid stay ten days ahead. `free_in`: hours until the free window ends (None = no window)."""
    free_until = timezone.now() + timedelta(hours=free_in) if free_in is not None else None
    return make_stay(
        world['prop'], world['guest'], world['today'] + timedelta(days=10), nights=2,
        room=world['room'], rate=world['rate'],
        cancel_free_until=free_until, cancel_refund_percent_after=percent, **kwargs)


def cancel(world, booking, capture, user=None):
    with capture(execute=True):
        return client_for(user or world['guest']).post(f'{BASE}/{booking.pk}/cancel/', {}, format='json')


def preview(world, booking, user=None):
    return client_for(user or world['guest']).get(f'{BASE}/{booking.pk}/cancel-preview/')


@pytest.mark.django_db
class TestCancelRefundsWhatWasPromised:

    def test_inside_the_free_window_everything_comes_back(self, world, django_capture_on_commit_callbacks):
        booking = stay(world, free_in=24)
        response = cancel(world, booking, django_capture_on_commit_callbacks)
        assert response.status_code == 200, response.data
        booking.refresh_from_db()
        assert booking.status == 'cancelled'
        refund = Refund.objects.get()
        assert (refund.booking_id, refund.reason, refund.amount, refund.currency) == (booking.pk, 'cancel', CHARGE, 'UZS')
        assert response.data['refund'] == {'amount': '2354590.00', 'currency': 'UZS', 'percent': 100}

    def test_after_the_free_window_the_percent_after_applies(self, world, django_capture_on_commit_callbacks):
        booking = stay(world, free_in=-1, percent=25)
        response = cancel(world, booking, django_capture_on_commit_callbacks)
        assert response.status_code == 200
        assert Refund.objects.get().amount == Decimal('588647.50').quantize(Decimal('1'), rounding='ROUND_HALF_UP')
        assert response.data['refund']['percent'] == 25

    def test_without_a_free_window_the_percent_applies_at_any_time(self, world, django_capture_on_commit_callbacks):
        booking = stay(world, free_in=None, percent=50)
        cancel(world, booking, django_capture_on_commit_callbacks)
        assert Refund.objects.get().amount == Decimal('1177295')

    def test_amounts_are_whole_som_rounded_half_up(self, world, django_capture_on_commit_callbacks):
        booking = stay(world, percent=33)
        cancel(world, booking, django_capture_on_commit_callbacks)
        assert Refund.objects.get().amount == Decimal('777015')       # 2 354 590 x 0.33 = 777 014.7

    def test_a_non_refundable_plan_cancels_without_a_refund(self, world, django_capture_on_commit_callbacks):
        booking = stay(world, percent=0)
        response = cancel(world, booking, django_capture_on_commit_callbacks)
        assert response.status_code == 200
        booking.refresh_from_db()
        assert booking.status == 'cancelled'
        assert not Refund.objects.exists()
        assert response.data['refund'] == {'amount': '0.00', 'currency': 'UZS', 'percent': 0}

    def test_a_booking_made_before_the_terms_existed_is_cancelled_with_no_automatic_refund(
            self, world, django_capture_on_commit_callbacks):
        booking = stay(world, percent=None)
        response = cancel(world, booking, django_capture_on_commit_callbacks)
        assert response.status_code == 200
        assert not Refund.objects.exists()
        assert response.data['refund'] == {'amount': '0.00', 'currency': 'UZS', 'percent': None}

    def test_an_unpaid_booking_is_cancelled_with_nothing_to_refund(self, world, django_capture_on_commit_callbacks):
        booking = stay(world, free_in=24, status='pending', paid=False)
        response = cancel(world, booking, django_capture_on_commit_callbacks)
        assert response.status_code == 200
        assert not Refund.objects.exists()
        assert response.data['refund']['amount'] == '0.00'

    def test_a_payment_that_is_not_completed_is_not_refunded(self, world, django_capture_on_commit_callbacks):
        booking = stay(world, free_in=24, paid=False)
        pay(booking, status='pending')
        cancel(world, booking, django_capture_on_commit_callbacks)
        assert not Refund.objects.exists()

    def test_the_refund_is_split_over_the_payments_never_above_what_each_paid(
            self, world, django_capture_on_commit_callbacks):
        booking = stay(world, free_in=24, paid=False)
        pay(booking, amount=Decimal('1000000'))
        pay(booking, amount=Decimal('1354590'))
        cancel(world, booking, django_capture_on_commit_callbacks)
        refunds = Refund.objects.all()
        assert sum(r.amount for r in refunds) == CHARGE
        assert all(r.amount <= r.payment.amount for r in refunds)
        assert refunds.count() == 2

    def test_what_was_already_refunded_is_not_refunded_twice(self, world, django_capture_on_commit_callbacks):
        booking = stay(world, free_in=24)
        Refund.objects.create(payment=booking.payment_transactions.get(), booking=booking, amount=Decimal('1000000'),
                              currency='UZS', reason='staff', status='succeeded', idempotency_key='earlier')
        cancel(world, booking, django_capture_on_commit_callbacks)
        later = Refund.objects.exclude(idempotency_key='earlier').get()
        assert later.amount == CHARGE - Decimal('1000000')


@pytest.mark.django_db
class TestCancelIsSafe:

    def test_a_second_cancel_is_refused_and_creates_no_second_refund(self, world, django_capture_on_commit_callbacks):
        booking = stay(world, free_in=24)
        assert cancel(world, booking, django_capture_on_commit_callbacks).status_code == 200
        again = cancel(world, booking, django_capture_on_commit_callbacks)
        assert again.status_code == 400
        assert Refund.objects.count() == 1

    def test_only_the_guest_can_cancel_their_booking(self, world, django_capture_on_commit_callbacks):
        booking = stay(world, free_in=24)
        for other in (world['owner'], world['other_owner'], world['staff']):
            response = cancel(world, booking, django_capture_on_commit_callbacks, user=other)
            assert response.status_code == 404
        booking.refresh_from_db()
        assert booking.status == 'confirmed'
        assert not Refund.objects.exists()

    def test_a_stay_that_has_started_cannot_be_cancelled_online(self, world, django_capture_on_commit_callbacks):
        booking = make_stay(world['prop'], world['guest'], world['today'], nights=2, room=world['room'],
                            rate=world['rate'], cancel_free_until=None, cancel_refund_percent_after=50)
        assert cancel(world, booking, django_capture_on_commit_callbacks).status_code == 400
        assert not Refund.objects.exists()

    def test_the_cancel_and_the_refund_stand_or_fall_together(self, world, monkeypatch, django_capture_on_commit_callbacks):
        import payments.refunds
        from bookings.cancellation import cancel_with_refund
        booking = stay(world, free_in=24)

        def boom(*args, **kwargs):
            raise RuntimeError('refund failed')
        monkeypatch.setattr(payments.refunds, 'create_refund', boom)
        with pytest.raises(RuntimeError):
            cancel_with_refund(booking, 'changed my mind')
        booking.refresh_from_db()
        assert booking.status == 'confirmed'
        assert not Refund.objects.exists()

    def test_the_refund_is_sent_to_the_provider_after_the_commit(self, world, django_capture_on_commit_callbacks):
        booking = stay(world, free_in=24)
        with django_capture_on_commit_callbacks(execute=False) as callbacks:
            client_for(world['guest']).post(f'{BASE}/{booking.pk}/cancel/', {}, format='json')
        assert len(callbacks) == 1
        assert Refund.objects.get().status == 'pending'


@pytest.mark.django_db
class TestCancelPreview:

    def test_in_the_free_window_it_shows_the_whole_payment(self, world):
        booking = stay(world, free_in=24)
        response = preview(world, booking)
        assert response.status_code == 200, response.data
        assert response.data['refund_amount'] == '2354590.00'
        assert response.data['refund_currency'] == 'UZS'
        assert response.data['refund_percent'] == 100
        assert response.data['free_until'] is not None

    def test_after_the_window_it_shows_the_percent_after(self, world):
        booking = stay(world, free_in=-1, percent=50)
        data = preview(world, booking).data
        assert (data['refund_amount'], data['refund_percent']) == ('1177295.00', 50)

    def test_it_changes_nothing(self, world):
        booking = stay(world, free_in=24)
        preview(world, booking)
        booking.refresh_from_db()
        assert booking.status == 'confirmed'
        assert not Refund.objects.exists()

    def test_an_unpaid_booking_shows_zero(self, world):
        booking = stay(world, free_in=24, status='pending', paid=False)
        assert preview(world, booking).data['refund_amount'] == '0.00'

    def test_a_booking_without_terms_shows_no_promise(self, world):
        booking = stay(world, percent=None)
        data = preview(world, booking).data
        assert (data['refund_amount'], data['refund_percent']) == ('0.00', None)

    def test_a_cancelled_booking_cannot_be_previewed(self, world):
        booking = stay(world, free_in=24, status='cancelled')
        assert preview(world, booking).status_code == 400

    def test_only_the_guest_sees_it(self, world):
        booking = stay(world, free_in=24)
        assert preview(world, booking, user=world['owner']).status_code == 404
        assert client_for(None).get(f'{BASE}/{booking.pk}/cancel-preview/').status_code in (401, 403)

    def test_the_booking_response_carries_the_terms(self, world):
        booking = stay(world, free_in=24, percent=40)
        data = client_for(world['guest']).get(f'{BASE}/{booking.pk}/').data
        assert data['cancellation_terms']['refund_percent_after'] == 40
        assert data['cancellation_terms']['free_until'] is not None
