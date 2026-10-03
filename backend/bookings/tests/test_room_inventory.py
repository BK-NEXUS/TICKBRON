"""
Rooms are counted per room type and date, not per rate plan (audit #31, Phase 3).

Before: every rate plan had its own DateInventory room count, so one physical room
could be sold once through each rate plan of its room type.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from bookings.models import Booking
from properties.models import DateInventory, Property, PropertyType, RatePlan, RoomInventory, RoomType
from users.models import User
from currency.testing import make_usd_rate


class RoomInventoryFixture(TestCase):
    def setUp(self):
        make_usd_rate()  # R6: a USD hotel is bookable only once a rate exists
        self.owner = User.objects.create_user(email='owner@example.com', password='x')
        self.guest = User.objects.create_user(email='guest@example.com', password='x')
        hotel = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.property = Property.objects.create(
            owner=self.owner, property_type=hotel, status='active', max_guests=4,
            address_line1='1 Main St', city='Tashkent', country='Uzbekistan', base_price=Decimal('60.00'),
        )
        # One physical room, sold through two rate plans
        self.room_type = RoomType.objects.create(
            property=self.property, name='Double', slug='double', base_occupancy=2, max_occupancy=2,
            base_price=Decimal('60.00'), total_rooms=1,
        )
        self.flexible = RatePlan.objects.create(
            room_type=self.room_type, name='Flexible', slug='flexible', base_price=Decimal('70.00'),
        )
        self.non_refundable = RatePlan.objects.create(
            room_type=self.room_type, name='Non-refundable', slug='non-refundable',
            rate_type='non_refundable', base_price=Decimal('60.00'),
        )
        self.check_in = timezone.localdate() + timedelta(days=10)
        self.check_out = self.check_in + timedelta(days=2)
        for rate_plan in (self.flexible, self.non_refundable):
            for offset in range(2):
                DateInventory.objects.create(
                    rate_plan=rate_plan, date=self.check_in + timedelta(days=offset),
                    available_rooms=1, price=rate_plan.base_price,
                )

    def book(self, rate_plan):
        return Booking.create_booking(
            guest=self.guest, property_obj=self.property, room_type=self.room_type, rate_plan=rate_plan,
            check_in=self.check_in, check_out=self.check_out, guest_count=2,
        )


class TestDoubleSellAcrossRatePlans(RoomInventoryFixture):
    def test_the_last_room_cannot_be_sold_again_through_another_rate_plan(self):
        self.book(self.flexible)

        with pytest.raises(ValidationError) as error:
            self.book(self.non_refundable)

        assert 'availability' in error.value.message_dict
        assert Booking.objects.filter(status='pending').count() == 1


class TestRoomInventoryModel(RoomInventoryFixture):
    def test_one_row_per_room_type_and_date(self):
        RoomInventory.objects.create(room_type=self.room_type, date=self.check_in, available_rooms=1)
        with pytest.raises(IntegrityError), transaction.atomic():
            RoomInventory.objects.create(room_type=self.room_type, date=self.check_in, available_rooms=1)

    def test_defaults(self):
        row = RoomInventory.objects.create(room_type=self.room_type, date=self.check_in, available_rooms=1)
        assert row.booked_rooms == 0
        assert row.is_available is True
        assert row.remaining_rooms == 1

    def test_available_rooms_cannot_exceed_total_rooms(self):
        row = RoomInventory(room_type=self.room_type, date=self.check_in, available_rooms=2)
        with pytest.raises(ValidationError) as error:
            row.full_clean()
        assert 'available_rooms' in error.value.message_dict

    def test_remaining_rooms_never_negative(self):
        row = RoomInventory(room_type=self.room_type, date=self.check_in, available_rooms=1, booked_rooms=3)
        assert row.remaining_rooms == 0

    def test_booked_rooms_cannot_be_negative_in_the_database(self):
        with pytest.raises(IntegrityError), transaction.atomic():
            RoomInventory.objects.create(
                room_type=self.room_type, date=self.check_in, available_rooms=1, booked_rooms=-1,
            )

