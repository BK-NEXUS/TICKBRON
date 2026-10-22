"""
Cash at the hotel (.ai/PLAN_CASH_ONLY.md stage 3): a guest cancels their booking at any time before the stay
starts, for free. There is no refund, no cancellation terms and no cancel-preview.

POST /bookings/{id}/cancel/  cancels the booking and releases the rooms (guest only)
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from bookings.models import Booking
from bookings.tests.r12b_helpers import client_for, make_stay, world  # noqa: F401
from properties.models import RoomInventory

BASE = '/api/v1/bookings'


def stay(world, days_ahead=10, **kwargs):
    return make_stay(
        world['prop'], world['guest'], world['today'] + timedelta(days=days_ahead), nights=2,
        room=world['room'], rate=world['rate'], **kwargs)


def cancel(world, booking, user=None):
    return client_for(user or world['guest']).post(f'{BASE}/{booking.pk}/cancel/', {}, format='json')


@pytest.mark.django_db
class TestCancelIsFree:

    def test_the_guest_cancels_at_any_time_before_the_stay(self, world):
        for days_ahead in (1, 10, 60):
            booking = stay(world, days_ahead)
            response = cancel(world, booking)
            assert response.status_code == 200, days_ahead
            assert response.data['status'] == 'cancelled'
            booking.refresh_from_db()
            assert booking.status == 'cancelled'

    def test_the_answer_carries_no_refund_and_no_terms(self, world):
        response = cancel(world, stay(world))
        for key in ('refund', 'cancellation_terms', 'no_show_refund_percent', 'no_show_refund_amount'):
            assert key not in response.data, key

    def test_the_booking_response_carries_no_refund_terms(self, world):
        booking = stay(world)
        data = client_for(world['guest']).get(f'{BASE}/{booking.pk}/').data
        for key in ('cancellation_terms', 'no_show_refund_percent', 'no_show_refund_amount',
                    'no_show_refund_text_key', 'no_show_refund_text_params'):
            assert key not in data, key

    def test_there_is_no_cancel_preview(self, world):
        booking = stay(world)
        assert client_for(world['guest']).get(f'{BASE}/{booking.pk}/cancel-preview/').status_code == 404

    def test_cancelling_releases_the_rooms(self, world):
        booking = stay(world)
        RoomInventory.objects.filter(room_type=world['room']).update(booked_rooms=1)
        assert cancel(world, booking).status_code == 200
        assert not RoomInventory.objects.filter(room_type=world['room'], booked_rooms__gt=0).exists()


@pytest.mark.django_db
class TestCancelIsSafe:

    def test_a_second_cancel_is_refused(self, world):
        booking = stay(world)
        assert cancel(world, booking).status_code == 200
        assert cancel(world, booking).status_code == 400

    def test_only_the_guest_can_cancel_their_booking(self, world):
        booking = stay(world)
        for other in (world['owner'], world['other_owner'], world['staff']):
            assert cancel(world, booking, user=other).status_code == 404
        booking.refresh_from_db()
        assert booking.status == 'confirmed'

    def test_an_anonymous_visitor_cannot_cancel(self, world):
        booking = stay(world)
        response = APIClient().post(f'{BASE}/{booking.pk}/cancel/', {}, format='json')
        assert response.status_code in (401, 403)
        assert Booking.objects.get(pk=booking.pk).status == 'confirmed'

    def test_a_stay_that_has_started_cannot_be_cancelled_online(self, world):
        booking = make_stay(world['prop'], world['guest'], world['today'], nights=2, room=world['room'],
                            rate=world['rate'])
        assert cancel(world, booking).status_code == 400
        booking.refresh_from_db()
        assert booking.status == 'confirmed'
