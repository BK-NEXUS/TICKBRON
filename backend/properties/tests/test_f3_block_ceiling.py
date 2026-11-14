"""
Security F3: a released block must never push available_rooms over the room type's total_rooms.

RoomBlock.release() added the blocked rooms back with no ceiling, and bulk_set() overwrote the block's
reduction, so releasing (or releasing twice at once) made available_rooms > total_rooms: more rooms for sale
than the hotel has (oversell).
"""
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import F
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from bookings.tests.test_concurrency import run_concurrently
from properties.models import Property, PropertyType, RoomBlock, RoomInventory, RoomType
from users.models import User


class BlockFixtureMixin:
    def build(self):
        self.owner = User.objects.create_user(email='f3block@example.com', password='x')
        prop = Property.objects.create(
            owner=self.owner, property_type=PropertyType.objects.create(name='Hotel', slug='hotel-f3b'),
            status='active', max_guests=2, address_line1='1 Main', city='Tashkent', country='Uzbekistan',
            base_price=Decimal('60.00'),
        )
        self.room_type = RoomType.objects.create(
            property=prop, name='Double', slug='double-f3b', base_occupancy=2, max_occupancy=2,
            base_price=Decimal('60.00'), total_rooms=5,
        )
        self.start = timezone.localdate() + timedelta(days=3)
        self.end = self.start + timedelta(days=1)

    def block(self, rooms=2):
        return RoomBlock.create_block(self.room_type, self.start, self.end, rooms, 'phone', self.owner)

    def row(self):
        return RoomInventory.objects.get(room_type=self.room_type, date=self.start)


class TestReleaseCeiling(BlockFixtureMixin, TestCase):
    def setUp(self):
        self.build()

    def test_release_after_bulk_set_does_not_exceed_total_rooms(self):
        block = self.block(2)
        RoomInventory.bulk_set(self.room_type, self.start, self.end, available_rooms=5)
        block.release()
        self.assertEqual(self.row().available_rooms, 5)

    def test_release_of_a_normal_block_restores_the_rooms(self):
        block = self.block(2)
        self.assertEqual(self.row().available_rooms, 3)
        block.release()
        self.assertEqual(self.row().available_rooms, 5)

    def test_releasing_the_same_block_twice_restores_the_rooms_once(self):
        block = self.block(2)
        RoomInventory.bulk_set(self.room_type, self.start, self.end, available_rooms=1)
        block.release()
        RoomBlock.objects.get(pk=block.pk).release()
        self.assertEqual(self.row().available_rooms, 3)


class TestInventoryConstraints(BlockFixtureMixin, TestCase):
    def setUp(self):
        self.build()

    def test_database_refuses_more_booked_than_available(self):
        RoomInventory.objects.create(room_type=self.room_type, date=self.start, available_rooms=3, booked_rooms=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            RoomInventory.objects.filter(room_type=self.room_type, date=self.start).update(
                booked_rooms=F('available_rooms') + 1)


class TestConcurrentRelease(BlockFixtureMixin, TransactionTestCase):
    def setUp(self):
        self.build()

    def test_two_simultaneous_releases_restore_the_rooms_once(self):
        block = self.block(2)
        first = RoomBlock.objects.get(pk=block.pk)
        second = RoomBlock.objects.get(pk=block.pk)
        run_concurrently(first.release, second.release)
        self.assertEqual(self.row().available_rooms, 5)
