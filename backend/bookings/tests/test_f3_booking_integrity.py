"""
Security F3: cancel/expiry never crash on a short inventory count, inactive room types cannot be sold,
an arrived guest is not auto-cancelled from a stale copy, and a huge total is a 400, not a 500.
"""
from datetime import time
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from bookings.arrival import cancel_if_unarrived
from bookings.models import Booking
from bookings.pricing import quote_stay
from bookings.tests.test_room_inventory import RoomInventoryFixture
from properties.models import DateInventory, RoomInventory


class TestBookingIntegrity(RoomInventoryFixture):
    def test_cancel_with_booked_rooms_already_zero_does_not_crash(self):
        booking = self.book(self.flexible)
        RoomInventory.objects.filter(room_type=self.room_type).update(booked_rooms=0)
        booking.cancel_booking('guest')
        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(set(RoomInventory.objects.values_list('booked_rooms', flat=True)), {0})

    def test_expiry_with_booked_rooms_already_zero_does_not_crash(self):
        booking = self.book(self.flexible)
        Booking.objects.filter(pk=booking.pk).update(status='pending')
        booking.refresh_from_db()
        RoomInventory.objects.filter(room_type=self.room_type).update(booked_rooms=0)
        booking.expire_booking()
        self.assertEqual(set(RoomInventory.objects.values_list('booked_rooms', flat=True)), {0})

    def test_inactive_room_type_cannot_be_quoted_or_booked(self):
        self.room_type.is_active = False
        self.room_type.save()
        with self.assertRaises(ValidationError):
            quote_stay(self.flexible, self.check_in, self.check_out)
        with self.assertRaises(ValidationError):
            self.book(self.flexible)
        self.assertFalse(Booking.objects.exists())

    def test_a_total_too_large_for_the_column_is_a_validation_error(self):
        DateInventory.objects.filter(rate_plan=self.flexible).update(price=Decimal('99999999.99'))
        self.room_type.total_rooms = 1000
        self.room_type.save()
        with self.assertRaises(ValidationError):
            quote_stay(self.flexible, self.check_in, self.check_out, number_of_rooms=1000)

    def test_arrived_guest_is_not_cancelled_from_a_stale_copy(self):
        booking = self.book(self.flexible)
        Booking.objects.filter(pk=booking.pk).update(expected_arrival_time=time(10, 0), status='confirmed')
        stale = Booking.objects.get(pk=booking.pk)
        Booking.objects.filter(pk=booking.pk).update(arrived_at=timezone.now())
        self.assertFalse(cancel_if_unarrived(stale))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')
        self.assertEqual(RoomInventory.objects.get(room_type=self.room_type, date=self.check_in).booked_rooms, 1)

    def test_unarrived_guest_is_cancelled(self):
        booking = self.book(self.flexible)
        self.assertTrue(cancel_if_unarrived(Booking.objects.get(pk=booking.pk)))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
