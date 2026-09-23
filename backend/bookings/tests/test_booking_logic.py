"""
Tests for booking business rules from the audit (#7, #13, #17, #19, #29).
"""
from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest import mock

import pytest
from django.core.exceptions import ValidationError
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


class TestMultiRoomBooking(BookingLogicTestBase):
    """#7: every booked room is priced and taken from inventory."""

    def test_price_and_inventory_scale_with_room_count(self):
        response = self.post_booking(nights=2, number_of_rooms=3)

        assert response.status_code == status.HTTP_201_CREATED
        assert Decimal(response.data['total_price']) == Decimal('600.00')  # 2 nights x 100 x 3 rooms
        assert self.inventory(0).booked_rooms == 3
        assert self.inventory(1).booked_rooms == 3

    def test_cancelling_multi_room_booking_releases_all_rooms(self):
        booking_id = self.post_booking(nights=2, number_of_rooms=3).data['id']

        response = self.client.post(f'{BOOKINGS_URL}{booking_id}/cancel/', {}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert self.inventory(0).booked_rooms == 0
        assert self.inventory(1).booked_rooms == 0

    def test_expiring_multi_room_booking_releases_all_rooms(self):
        booking = self.create_booking(nights=1, number_of_rooms=2)
        self.expire_now(booking)

        Booking.process_expired_bookings(raise_on_error=True)

        assert self.inventory(0).booked_rooms == 0

    def test_more_rooms_than_remaining_is_rejected(self):
        self.create_booking(nights=1, number_of_rooms=4)  # 1 room left

        response = self.post_booking(nights=1, number_of_rooms=2)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert self.inventory(0).booked_rooms == 4

    def test_zero_rooms_is_rejected(self):
        with pytest.raises(ValidationError):
            self.create_booking(nights=1, number_of_rooms=0)
        assert self.inventory(0).booked_rooms == 0


class TestBookingInputValidation(BookingLogicTestBase):
    """#19: past dates, room capacity and the stored nightly price."""

    def test_past_check_in_is_rejected(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        DateInventory.objects.create(
            rate_plan=self.rate_plan, date=yesterday, available_rooms=5, booked_rooms=0,
            price=Decimal('100.00'), currency='USD', is_available=True
        )

        response = self.post_booking(check_in=yesterday)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        with pytest.raises(ValidationError):
            self.create_booking(day_offset=-(self.start - yesterday).days)
        assert not Booking.objects.exists()

    def test_check_in_today_is_allowed(self):
        today = timezone.localdate()
        DateInventory.objects.create(
            rate_plan=self.rate_plan, date=today, available_rooms=5, booked_rooms=0,
            price=Decimal('100.00'), currency='USD', is_available=True
        )

        response = self.post_booking(check_in=today)

        assert response.status_code == status.HTTP_201_CREATED

    def test_guest_count_is_checked_against_all_booked_rooms(self):
        # max_occupancy is 4 per room
        assert self.post_booking(number_of_rooms=2, guest_count=8).status_code == status.HTTP_201_CREATED
        assert self.post_booking(number_of_rooms=2, guest_count=9).status_code == status.HTTP_400_BAD_REQUEST
        with pytest.raises(ValidationError):
            self.create_booking(number_of_rooms=1, guest_count=5)

    def test_price_per_night_is_average_inventory_price(self):
        DateInventory.objects.filter(rate_plan=self.rate_plan, date=self.start).update(price=Decimal('100.00'))
        DateInventory.objects.filter(
            rate_plan=self.rate_plan, date=self.start + timedelta(days=1)
        ).update(price=Decimal('150.00'))
        DateInventory.objects.filter(
            rate_plan=self.rate_plan, date=self.start + timedelta(days=2)
        ).update(price=Decimal('155.00'))

        booking = self.create_booking(nights=3, number_of_rooms=2)

        item = booking.booking_items.get()
        assert item.price_per_night == Decimal('135.00')  # (100 + 150 + 155) / 3
        assert booking.total_price == Decimal('810.00')  # 405 x 2 rooms

    def test_availability_rejects_past_dates(self):
        yesterday = timezone.localdate() - timedelta(days=1)

        response = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': str(yesterday), 'check_out': str(self.start)}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestOnlyActivePropertiesArePublic(BookingLogicTestBase):
    """#13: only approved (status='active') properties can be booked or seen publicly."""

    NON_ACTIVE_STATUSES = ('draft', 'pending_approval', 'suspended', 'rejected')

    def set_status(self, value):
        Property.objects.filter(pk=self.property.pk).update(status=value)
        self.property.refresh_from_db()

    def test_non_active_property_cannot_be_booked(self):
        for value in self.NON_ACTIVE_STATUSES:
            self.set_status(value)

            assert self.post_booking().status_code == status.HTTP_400_BAD_REQUEST, value
            with pytest.raises(ValidationError):
                self.create_booking()
        assert not Booking.objects.exists()

    def test_non_active_property_is_hidden_from_public_endpoints(self):
        public = APIClient()
        for value in self.NON_ACTIVE_STATUSES:
            self.set_status(value)

            detail = public.get(f'/api/v1/properties/{self.property.id}/')
            availability = public.get(f'/api/v1/properties/{self.property.id}/availability/')
            suggestions = public.get('/api/v1/properties/search/suggestions/', {'q': 'Tashk'})

            assert detail.status_code == status.HTTP_404_NOT_FOUND, value
            assert availability.status_code == status.HTTP_404_NOT_FOUND, value
            assert 'Tashkent' not in suggestions.data['suggestions'], value

    def test_active_property_is_still_public_and_bookable(self):
        public = APIClient()

        assert public.get(f'/api/v1/properties/{self.property.id}/').status_code == status.HTTP_200_OK
        assert public.get(f'/api/v1/properties/{self.property.id}/availability/').status_code == status.HTTP_200_OK
        assert 'Tashkent' in public.get('/api/v1/properties/search/suggestions/', {'q': 'Tashk'}).data['suggestions']
        assert self.post_booking().status_code == status.HTTP_201_CREATED


class TestExpiredBookingTask(BookingLogicTestBase):
    """#17: a Celery beat task expires pending bookings; expired bookings cannot be paid."""

    def test_task_expires_overdue_bookings_and_releases_rooms(self):
        from bookings.tasks import expire_pending_bookings

        overdue = self.create_booking(day_offset=0, number_of_rooms=2)
        fresh = self.create_booking(day_offset=0)
        self.expire_now(overdue)

        processed = expire_pending_bookings.apply().get()

        assert processed == 1
        overdue.refresh_from_db()
        fresh.refresh_from_db()
        assert overdue.status == 'cancelled'
        assert fresh.status == 'pending'
        assert self.inventory(0).booked_rooms == 1

    def test_task_is_scheduled_in_celery_beat(self):
        from django.conf import settings

        from config.celery import app

        schedule = settings.CELERY_BEAT_SCHEDULE['expire-pending-bookings']
        assert schedule['task'] == 'bookings.tasks.expire_pending_bookings'
        assert schedule['schedule'] <= 15 * 60  # bookings expire after 15 minutes
        assert app.conf.beat_schedule['expire-pending-bookings']['task'] == schedule['task']

    def test_task_fails_visibly_when_a_booking_cannot_be_expired(self):
        from bookings.tasks import expire_pending_bookings

        booking = self.create_booking()
        self.expire_now(booking)

        with mock.patch.object(Booking, 'expire_booking', side_effect=RuntimeError('boom')):
            with self.assertLogs('bookings.models', level='ERROR'):
                result = expire_pending_bookings.apply()

        assert result.failed()
        assert isinstance(result.result, ExpiredBookingProcessingError)

    def test_payment_cannot_start_for_expired_booking(self):
        booking = self.create_booking()
        self.expire_now(booking)

        response = self.client.post('/api/v1/payments/transactions/', {
            'idempotency_key': 'k-expired', 'booking': booking.id, 'provider': 'payme',
            'amount': str(booking.total_price), 'currency': 'USD',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'booking' in response.data['error']['details']
