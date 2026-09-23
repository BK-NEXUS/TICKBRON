"""
Real concurrency tests for booking state transitions (audit #18).

These need PostgreSQL: SQLite has no row-level locks and serializes writers,
so the races cannot happen there. Run with the PostgreSQL settings from .env:

    pytest --create-db bookings/tests/test_concurrency.py
"""
import threading
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TransactionTestCase
from django.utils import timezone

from bookings.models import Booking
from properties.models import DateInventory, Property, PropertyType, RatePlan, RoomType
from users.models import User


def run_concurrently(*calls):
    """
    Start every call at the same moment in its own thread and DB connection.

    Returns one ('ok', result) or ('error', exception) tuple per call.
    """
    barrier = threading.Barrier(len(calls))
    results = [None] * len(calls)

    def worker(index, call):
        try:
            barrier.wait(timeout=10)
            results[index] = ('ok', call())
        except Exception as exc:  # collected and asserted by the test
            results[index] = ('error', exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(i, call)) for i, call in enumerate(calls)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert all(not thread.is_alive() for thread in threads), 'a worker thread hung (deadlock?)'
    return results


class BookingConcurrencyTests(TransactionTestCase):
    """Two requests act on the same booking at the same time."""

    def setUp(self):
        if connection.vendor != 'postgresql':
            self.skipTest('Row-level locking races need PostgreSQL')

        self.user = User.objects.create_user(email='race@example.com', password='testpass123')
        property_type = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.property = Property.objects.create(
            owner=self.user, property_type=property_type, status='active',
            max_guests=4, bedrooms=1, bathrooms=1, city='Tashkent', country='Uzbekistan',
            base_price=Decimal('100.00'), currency='USD'
        )
        self.room_type = RoomType.objects.create(
            property=self.property, name='Standard', slug='standard', base_occupancy=2,
            max_occupancy=4, base_price=Decimal('100.00'), currency='USD', total_rooms=5
        )
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type, name='Standard Rate', slug='standard-rate', rate_type='standard',
            base_price=Decimal('100.00'), currency='USD', min_nights=1, max_nights=30, is_active=True
        )
        self.day = timezone.localdate() + timedelta(days=5)
        self.inventory = DateInventory.objects.create(
            rate_plan=self.rate_plan, date=self.day, available_rooms=5, booked_rooms=0,
            price=Decimal('100.00'), currency='USD', is_available=True
        )
        # Two bookings hold the night, so a double release shows up as 0 instead
        # of tripping the booked_rooms >= 0 check constraint
        self.other_booking = self._book()
        self.booking = self._book()
        assert self._booked_rooms() == 2

    def _book(self):
        return Booking.create_booking(
            guest=self.user, property_obj=self.property, room_type=self.room_type, rate_plan=self.rate_plan,
            check_in=self.day, check_out=self.day + timedelta(days=1), guest_count=2
        )

    def _booked_rooms(self):
        return DateInventory.objects.get(pk=self.inventory.pk).booked_rooms

    def _stale_copies(self, count=2):
        """Independent in-memory copies loaded before the race, as two requests would have."""
        return [Booking.objects.get(pk=self.booking.pk) for _ in range(count)]

    @staticmethod
    def _outcomes(results):
        return sorted(kind for kind, _ in results)

    def _assert_losers_got_validation_errors(self, results):
        for kind, value in results:
            if kind == 'error':
                assert isinstance(value, ValidationError), repr(value)

    def test_double_cancel_releases_inventory_once(self):
        first, second = self._stale_copies()

        results = run_concurrently(first.cancel_booking, second.cancel_booking)

        assert self._outcomes(results) == ['error', 'ok']
        self._assert_losers_got_validation_errors(results)
        assert self._booked_rooms() == 1
        assert Booking.objects.get(pk=self.booking.pk).status == 'cancelled'

    def test_cancel_and_expire_release_inventory_once(self):
        to_cancel, to_expire = self._stale_copies()

        results = run_concurrently(to_cancel.cancel_booking, to_expire.expire_booking)

        assert self._outcomes(results) == ['error', 'ok']
        self._assert_losers_got_validation_errors(results)
        assert self._booked_rooms() == 1

    def test_cancel_and_confirm_leave_a_consistent_booking(self):
        to_cancel, to_confirm = self._stale_copies()

        results = run_concurrently(to_cancel.cancel_booking, to_confirm.confirm_booking)

        # Both orders are legal once serialized: cancel first makes the confirm
        # fail (cancelled -> confirmed is invalid); confirm first lets the cancel
        # succeed afterwards (confirmed -> cancelled is allowed).
        self._assert_losers_got_validation_errors(results)
        booking = Booking.objects.get(pk=self.booking.pk)
        cancel_result, confirm_result = results
        if confirm_result[0] == 'error':
            assert cancel_result[0] == 'ok'
            assert (booking.status, booking.payment_status) == ('cancelled', 'pending')
        else:
            # Confirm ran first; the cancel saw the confirmed booking and still won
            assert cancel_result[0] == 'ok'
            assert (booking.status, booking.payment_status) == ('cancelled', 'paid')
        # Either way the cancelled booking released its room exactly once
        assert self._booked_rooms() == 1

    def test_last_room_cannot_be_sold_twice(self):
        DateInventory.objects.filter(pk=self.inventory.pk).update(available_rooms=3)  # 2 held, 1 left

        results = run_concurrently(self._book, self._book)

        assert self._outcomes(results) == ['error', 'ok']
        self._assert_losers_got_validation_errors(results)
        assert self._booked_rooms() == 3
