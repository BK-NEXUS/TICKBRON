"""
Tests for RoomInventory.bulk_set and DateInventory.bulk_set_price (3.6/3.7): the
calendar UI's date-range room-count/open-close edit and the bulk price edit.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from properties.models import (
    DateInventory, Property, PropertyType, RatePlan, RoomInventory, RoomType,
)
from users.models import User


class RoomInventoryBulkSetTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner-bulk@example.com', password='x')
        self.property_type = PropertyType.objects.create(name='Hotel', slug='hotel-bulk')
        self.property = Property.objects.create(
            owner=self.owner, property_type=self.property_type, status='active',
            max_guests=2, bedrooms=1, bathrooms=1, address_line1='1 Bulk St',
            city='Tashkent', country='Uzbekistan', base_price=50.00, currency='USD',
        )
        self.room_type = RoomType.objects.create(
            property=self.property, name='Room', slug='room-bulk',
            base_occupancy=2, max_occupancy=2, base_price=50.00, currency='USD', total_rooms=5,
        )
        self.start = date.today() + timedelta(days=1)
        self.end = self.start + timedelta(days=3)

    def test_sets_available_rooms_for_every_night_creating_unmanaged_rows(self):
        rows = RoomInventory.bulk_set(self.room_type, self.start, self.end, available_rooms=2)
        self.assertEqual(len(rows), 3)
        for offset in range(3):
            row = RoomInventory.objects.get(room_type=self.room_type, date=self.start + timedelta(days=offset))
            self.assertEqual(row.available_rooms, 2)

    def test_sets_is_available_only_leaves_available_rooms_untouched(self):
        RoomInventory.objects.create(room_type=self.room_type, date=self.start, available_rooms=4, booked_rooms=0)
        RoomInventory.bulk_set(self.room_type, self.start, self.start + timedelta(days=1), is_available=False)
        row = RoomInventory.objects.get(room_type=self.room_type, date=self.start)
        self.assertFalse(row.is_available)
        self.assertEqual(row.available_rooms, 4)

    def test_cannot_set_below_booked_rooms_error_names_the_date(self):
        booked_date = self.start + timedelta(days=1)
        RoomInventory.objects.create(room_type=self.room_type, date=booked_date, available_rooms=5, booked_rooms=3)
        with self.assertRaises(ValidationError) as ctx:
            RoomInventory.bulk_set(self.room_type, self.start, self.end, available_rooms=2)
        self.assertIn(booked_date.isoformat(), str(ctx.exception))
        # nothing partially applied
        row = RoomInventory.objects.get(room_type=self.room_type, date=booked_date)
        self.assertEqual(row.available_rooms, 5)
        self.assertFalse(RoomInventory.objects.filter(room_type=self.room_type, date=self.start).exists())

    def test_cannot_exceed_room_type_total(self):
        with self.assertRaises(ValidationError):
            RoomInventory.bulk_set(self.room_type, self.start, self.end, available_rooms=6)

    def test_date_to_must_be_after_date_from(self):
        with self.assertRaises(ValidationError):
            RoomInventory.bulk_set(self.room_type, self.start, self.start, available_rooms=1)

    def test_nothing_to_update_is_an_error(self):
        with self.assertRaises(ValidationError):
            RoomInventory.bulk_set(self.room_type, self.start, self.end)


class DateInventoryBulkSetPriceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner-bulkprice@example.com', password='x')
        self.property_type = PropertyType.objects.create(name='Hotel', slug='hotel-bulkprice')
        self.property = Property.objects.create(
            owner=self.owner, property_type=self.property_type, status='active',
            max_guests=2, bedrooms=1, bathrooms=1, address_line1='1 Price St',
            city='Tashkent', country='Uzbekistan', base_price=50.00, currency='USD',
        )
        self.room_type = RoomType.objects.create(
            property=self.property, name='Room', slug='room-bulkprice',
            base_occupancy=2, max_occupancy=2, base_price=50.00, currency='USD', total_rooms=4,
        )
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type, name='Standard', slug='standard-bulkprice', rate_type='standard',
            base_price=50.00, currency='USD', min_nights=1, is_active=True,
        )
        self.start = date.today() + timedelta(days=1)
        self.end = self.start + timedelta(days=3)

    def test_creates_rows_with_the_price_for_every_night(self):
        rows = DateInventory.bulk_set_price(self.rate_plan, self.start, self.end, Decimal('75.00'))
        self.assertEqual(len(rows), 3)
        for offset in range(3):
            row = DateInventory.objects.get(rate_plan=self.rate_plan, date=self.start + timedelta(days=offset))
            self.assertEqual(row.price, Decimal('75.00'))
            self.assertEqual(row.available_rooms, 4)  # defaults to the room type's total
            self.assertTrue(row.is_available)

    def test_updates_price_of_an_existing_row_without_touching_its_rules(self):
        DateInventory.objects.create(
            rate_plan=self.rate_plan, date=self.start, available_rooms=4, booked_rooms=1,
            price=Decimal('50.00'), currency='USD', is_available=False, minimum_stay=2,
        )
        DateInventory.bulk_set_price(self.rate_plan, self.start, self.start + timedelta(days=1), Decimal('99.00'))
        row = DateInventory.objects.get(rate_plan=self.rate_plan, date=self.start)
        self.assertEqual(row.price, Decimal('99.00'))
        self.assertEqual(row.booked_rooms, 1)
        self.assertFalse(row.is_available)
        self.assertEqual(row.minimum_stay, 2)

    def test_negative_price_is_rejected(self):
        with self.assertRaises(ValidationError):
            DateInventory.bulk_set_price(self.rate_plan, self.start, self.end, Decimal('-1.00'))

    def test_date_to_must_be_after_date_from(self):
        with self.assertRaises(ValidationError):
            DateInventory.bulk_set_price(self.rate_plan, self.start, self.start, Decimal('10.00'))
