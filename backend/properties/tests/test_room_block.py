"""
Tests for RoomBlock (3.5, external bookings/blocks): a hotel owner takes rooms out of
sale for a date range (e.g. sold through Booking.com or by phone) without a TICKBRON
booking. Blocks reduce RoomInventory.available_rooms and can be undone (deleted).
"""
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from properties.models import Property, PropertyType, RoomType, RoomInventory, RoomBlock
from users.models import User


class RoomBlockCreationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner-block@example.com', password='x')
        self.property_type = PropertyType.objects.create(name='Hotel', slug='hotel-block')
        self.property = Property.objects.create(
            owner=self.owner, property_type=self.property_type, status='active',
            max_guests=2, bedrooms=1, bathrooms=1, address_line1='1 Block St',
            city='Tashkent', country='Uzbekistan', base_price=50.00, currency='USD',
        )
        self.room_type = RoomType.objects.create(
            property=self.property, name='Room', slug='room-block',
            base_occupancy=2, max_occupancy=2, base_price=50.00, currency='USD', total_rooms=5,
        )
        self.start = date.today() + timedelta(days=1)
        self.end = self.start + timedelta(days=3)  # 3 nights

    def test_block_reduces_available_rooms_for_every_night(self):
        RoomBlock.create_block(
            room_type=self.room_type, date_from=self.start, date_to=self.end,
            rooms=2, note='Booking.com', created_by=self.owner,
        )
        for offset in range(3):
            row = RoomInventory.objects.get(room_type=self.room_type, date=self.start + timedelta(days=offset))
            self.assertEqual(row.available_rooms, 3)  # 5 - 2

    def test_block_on_unmanaged_nights_creates_room_inventory_rows(self):
        # No RoomInventory row exists yet -- unmanaged, opens at total_rooms.
        self.assertFalse(RoomInventory.objects.filter(room_type=self.room_type).exists())
        RoomBlock.create_block(
            room_type=self.room_type, date_from=self.start, date_to=self.end,
            rooms=1, note='phone', created_by=self.owner,
        )
        self.assertEqual(RoomInventory.objects.filter(room_type=self.room_type).count(), 3)

    def test_block_cannot_push_below_rooms_already_booked(self):
        booked_date = self.start + timedelta(days=1)
        RoomInventory.objects.create(
            room_type=self.room_type, date=booked_date, available_rooms=5, booked_rooms=4,
        )
        with self.assertRaises(ValidationError) as ctx:
            RoomBlock.create_block(
                room_type=self.room_type, date_from=self.start, date_to=self.end,
                rooms=2, note='Booking.com', created_by=self.owner,
            )
        self.assertIn(booked_date.isoformat(), str(ctx.exception))
        # nothing partially applied
        self.assertFalse(RoomBlock.objects.filter(room_type=self.room_type).exists())
        row = RoomInventory.objects.get(room_type=self.room_type, date=booked_date)
        self.assertEqual(row.available_rooms, 5)

    def test_block_exactly_up_to_remaining_rooms_is_allowed(self):
        RoomInventory.objects.create(
            room_type=self.room_type, date=self.start, available_rooms=5, booked_rooms=3,
        )
        # remaining = 2, blocking exactly 2 is fine
        RoomBlock.create_block(
            room_type=self.room_type, date_from=self.start, date_to=self.start + timedelta(days=1),
            rooms=2, note='phone', created_by=self.owner,
        )
        row = RoomInventory.objects.get(room_type=self.room_type, date=self.start)
        self.assertEqual(row.available_rooms, 3)
        self.assertEqual(row.remaining_rooms, 0)

    def test_release_restores_rooms_and_soft_deletes(self):
        block = RoomBlock.create_block(
            room_type=self.room_type, date_from=self.start, date_to=self.end,
            rooms=2, note='Booking.com', created_by=self.owner,
        )
        block.release()
        for offset in range(3):
            row = RoomInventory.objects.get(room_type=self.room_type, date=self.start + timedelta(days=offset))
            self.assertEqual(row.available_rooms, 5)
        self.assertTrue(RoomBlock.objects.get(pk=block.pk).is_deleted)

    def test_date_to_must_be_after_date_from(self):
        with self.assertRaises(ValidationError):
            RoomBlock.create_block(
                room_type=self.room_type, date_from=self.start, date_to=self.start,
                rooms=1, note='phone', created_by=self.owner,
            )
