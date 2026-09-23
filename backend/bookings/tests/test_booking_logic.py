"""
Tests for booking business rules from the audit (#7, #13, #17, #19, #29).
"""
from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest import mock

import pytest
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from bookings.models import Booking, ExpiredBookingProcessingError
from properties.models import DateInventory, Property, PropertyType, RatePlan, RoomType
from users.models import User

BOOKINGS_URL = '/api/v1/bookings/'


class BookingLogicTestBase(TestCase):
    """An active property with one room type (5 rooms, 4 guests each) and 10 days of inventory."""

    def setUp(self):
        self.user = User.objects.create_user(email='guest@example.com', password='testpass123')
        property_type = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.property = Property.objects.create(
            owner=self.user, property_type=property_type, status='active',
            max_guests=8, bedrooms=2, bathrooms=1, city='Tashkent', country='Uzbekistan',
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
        self.start = timezone.localdate() + timedelta(days=5)
        for offset in range(10):
            DateInventory.objects.create(
                rate_plan=self.rate_plan, date=self.start + timedelta(days=offset), available_rooms=5,
                booked_rooms=0, price=Decimal('100.00'), currency='USD', is_available=True
            )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def inventory(self, day_offset=0):
        return DateInventory.objects.get(rate_plan=self.rate_plan, date=self.start + timedelta(days=day_offset))

    def create_booking(self, nights=1, day_offset=0, **extra):
        check_in = self.start + timedelta(days=day_offset)
        return Booking.create_booking(
            guest=self.user, property_obj=self.property, room_type=self.room_type, rate_plan=self.rate_plan,
            check_in=check_in, check_out=check_in + timedelta(days=nights),
            guest_count=extra.pop('guest_count', 2), **extra
        )

    def post_booking(self, nights=1, day_offset=0, check_in=None, **extra):
        check_in = check_in or self.start + timedelta(days=day_offset)
        data = {
            'property_id': self.property.id, 'room_type_id': self.room_type.id, 'rate_plan_id': self.rate_plan.id,
            'check_in': str(check_in), 'check_out': str(check_in + timedelta(days=nights)), 'guest_count': 2,
        }
        data.update(extra)
        return self.client.post(BOOKINGS_URL, data, format='json')

    def expire_now(self, booking):
        Booking.objects.filter(pk=booking.pk).update(expires_at=timezone.now() - timedelta(minutes=1))


class TestExpiredBookingErrors(BookingLogicTestBase):
    """#29: failures while expiring bookings are logged and reported, not swallowed."""

    def setUp(self):
        super().setUp()
        self.good = self.create_booking(day_offset=0)
        self.bad = self.create_booking(day_offset=1)
        self.expire_now(self.good)
        self.expire_now(self.bad)
        original = Booking.expire_booking
        bad_pk = self.bad.pk

        def failing_expire(booking):
            if booking.pk == bad_pk:
                raise RuntimeError('boom')
            return original(booking)

        self.patch = mock.patch.object(Booking, 'expire_booking', failing_expire)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_one_failure_does_not_stop_the_others_and_is_logged(self):
        with self.assertLogs('bookings.models', level='ERROR') as logs:
            processed = Booking.process_expired_bookings()

        assert processed == 1
        self.good.refresh_from_db()
        assert self.good.status == 'cancelled'
        assert any(f'Failed to expire booking {self.bad.pk}' in line for line in logs.output)

    def test_raise_on_error_reports_failures_after_processing_all(self):
        with self.assertLogs('bookings.models', level='ERROR'):
            with pytest.raises(ExpiredBookingProcessingError, match=str(self.bad.pk)):
                Booking.process_expired_bookings(raise_on_error=True)

        self.good.refresh_from_db()
        assert self.good.status == 'cancelled'

    def test_management_command_exits_with_error(self):
        with self.assertLogs('core.management.commands.process_expired_bookings', level='ERROR'):
            with pytest.raises(CommandError):
                call_command('process_expired_bookings', stdout=StringIO())
