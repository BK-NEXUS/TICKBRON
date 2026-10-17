"""R11: the cancellation terms of the rate plan are copied onto the booking when it is created and never change."""
from datetime import timedelta

import pytest

from bookings.cancellation import free_until
from bookings.models import Booking
from bookings.tests.r12b_helpers import world  # noqa: F401
from properties.models import DateInventory, RoomInventory


@pytest.fixture
def stay_start(world):
    start = world['today'] + timedelta(days=30)
    for offset in range(3):
        day = start + timedelta(days=offset)
        RoomInventory.objects.create(room_type=world['room'], date=day, available_rooms=3, booked_rooms=0)
        DateInventory.objects.create(rate_plan=world['rate'], date=day, available_rooms=3, booked_rooms=0,
                                     price=500000, currency='UZS', is_available=True)
    return start


def book(world, start):
    return Booking.create_booking(
        guest=world['guest'], property_obj=world['prop'], room_type=world['room'], rate_plan=world['rate'],
        check_in=start, check_out=start + timedelta(days=2), guest_count=2,
    )


@pytest.mark.django_db
class TestSnapshotAtCreation:

    def test_a_plan_with_nothing_set_gives_the_platform_percent_and_no_free_window(self, world, stay_start):
        booking = book(world, stay_start)
        assert booking.cancel_free_until is None
        assert booking.cancel_refund_percent_after == 50

    def test_the_plans_free_window_and_percent_are_stored(self, world, stay_start):
        world['rate'].free_cancel_hours = 48
        world['rate'].cancel_refund_percent = 25
        world['rate'].save()
        booking = book(world, stay_start)
        assert booking.cancel_free_until == free_until(stay_start, 48)
        assert booking.cancel_refund_percent_after == 25

    def test_a_non_refundable_plan_stores_zero_not_the_platform_percent(self, world, stay_start):
        world['rate'].cancel_refund_percent = 0
        world['rate'].save()
        assert book(world, stay_start).cancel_refund_percent_after == 0

    def test_the_stored_row_has_the_terms(self, world, stay_start):
        world['rate'].free_cancel_hours = 24
        world['rate'].save()
        booking = book(world, stay_start)
        booking.refresh_from_db()
        assert booking.cancel_free_until == free_until(stay_start, 24)

    def test_a_later_change_of_the_plan_does_not_touch_a_booking_already_made(self, world, stay_start):
        world['rate'].free_cancel_hours = 48
        world['rate'].cancel_refund_percent = 80
        world['rate'].save()
        booking = book(world, stay_start)
        world['rate'].free_cancel_hours = None
        world['rate'].cancel_refund_percent = 0
        world['rate'].save()
        booking.refresh_from_db()
        assert booking.cancel_free_until == free_until(stay_start, 48)
        assert booking.cancel_refund_percent_after == 80

    def test_a_later_change_of_the_platform_percent_does_not_touch_it_either(self, world, stay_start, settings):
        booking = book(world, stay_start)
        settings.CANCEL_REFUND_PERCENT = 10
        booking.refresh_from_db()
        assert booking.cancel_refund_percent_after == 50

    def test_the_terms_cannot_be_rewritten_on_the_row(self, world, stay_start):
        booking = Booking.objects.get(pk=book(world, stay_start).pk)
        booking.cancel_refund_percent_after = 100
        with pytest.raises(PermissionError):
            booking.save()
