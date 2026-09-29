"""
Migration 0008 backfills RoomInventory from DateInventory + active bookings
(audit #31, Phase 3 step 3.2).

Runs the real migration executor against the test database, so it migrates
the schema back and forth and truncates tables as it goes. Keep these out of
the normal test run:

    pytest --create-db properties/tests/test_room_inventory_migration.py
"""
from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class Migrate0007To0008(TransactionTestCase):
    """Migrates the test database from 0007 to 0008 and back, with historical models."""

    migrate_from = [
        ('properties', '0007_room_inventory'),
        ('bookings', '0004_booking_reference_code'),
        ('users', '0006_user_phone_number_unique'),
    ]
    migrate_to = [
        ('properties', '0008_populate_room_inventory'),
        ('bookings', '0004_booking_reference_code'),
        ('users', '0006_user_phone_number_unique'),
    ]

    def setUp(self):
        super().setUp()
        if connection.vendor != 'postgresql':
            self.skipTest('Migration executor tests need PostgreSQL')

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        executor.loader.build_graph()
        self.old_apps = executor.loader.project_state(self.migrate_from).apps
        self._executor = executor

    def tearDown(self):
        # Always land back on the latest migration for whatever test runs next.
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def migrate_forward(self):
        executor = self._executor
        executor.loader.build_graph()
        executor.migrate(self.migrate_to)
        executor.loader.build_graph()
        return executor.loader.project_state(self.migrate_to).apps

    def _seed_common(self, apps):
        User = apps.get_model('users', 'User')
        PropertyType = apps.get_model('properties', 'PropertyType')
        Property = apps.get_model('properties', 'Property')
        RoomType = apps.get_model('properties', 'RoomType')
        RatePlan = apps.get_model('properties', 'RatePlan')

        owner = User.objects.create(email='owner@example.com', password='x')
        hotel = PropertyType.objects.create(name='Hotel', slug='hotel')
        prop = Property.objects.create(
            owner=owner, property_type=hotel, status='active', max_guests=4,
            address_line1='1 Main St', city='Tashkent', country='Uzbekistan',
            base_price=Decimal('60.00'),
        )
        room_type = RoomType.objects.create(
            property=prop, name='Double', slug='double', base_occupancy=2, max_occupancy=2,
            base_price=Decimal('60.00'), total_rooms=3,
        )
        rate_a = RatePlan.objects.create(
            room_type=room_type, name='Flexible', slug='flexible', base_price=Decimal('70.00'),
        )
        rate_b = RatePlan.objects.create(
            room_type=room_type, name='Non-refundable', slug='non-refundable',
            rate_type='non_refundable', base_price=Decimal('60.00'),
        )
        return owner, room_type, rate_a, rate_b

    def test_available_is_the_max_over_rate_plans_capped_at_total_rooms(self):
        apps = self.old_apps
        DateInventory = apps.get_model('properties', 'DateInventory')
        _, room_type, rate_a, rate_b = self._seed_common(apps)
        day = timezone.localdate() + timedelta(days=10)

        # total_rooms=3; rate_a offers 2, rate_b offers 5 -> capped at 3
        DateInventory.objects.create(rate_plan=rate_a, date=day, available_rooms=2, price=Decimal('70'))
        DateInventory.objects.create(rate_plan=rate_b, date=day, available_rooms=5, price=Decimal('60'))

        new_apps = self.migrate_forward()
        RoomInventory = new_apps.get_model('properties', 'RoomInventory')
        row = RoomInventory.objects.get(room_type_id=room_type.pk, date=day)
        self.assertEqual(row.available_rooms, 3)

    def test_booked_rooms_come_from_active_bookings_not_old_counters(self):
        apps = self.old_apps
        DateInventory = apps.get_model('properties', 'DateInventory')
        Booking = apps.get_model('bookings', 'Booking')
        BookingItem = apps.get_model('bookings', 'BookingItem')
        User = apps.get_model('users', 'User')
        owner, room_type, rate_a, rate_b = self._seed_common(apps)
        guest = User.objects.create(email='guest@example.com', password='x')
        day = timezone.localdate() + timedelta(days=10)

        # Old counter says 1 booked; the real bookings below say 2 rooms are held.
        DateInventory.objects.create(
            rate_plan=rate_a, date=day, available_rooms=3, booked_rooms=1, price=Decimal('70'),
        )
        pending = Booking.objects.create(
            guest=guest, property=room_type.property, status='pending', payment_status='pending',
            check_in=day, check_out=day + timedelta(days=1), number_of_nights=1, guest_count=2,
            total_price=Decimal('70'), number_of_rooms=1, confirmation_code='AAAAA1',
        )
        BookingItem.objects.create(
            booking=pending, room_type=room_type, rate_plan=rate_a, number_of_rooms=1,
            price_per_night=Decimal('70'),
        )
        confirmed = Booking.objects.create(
            guest=guest, property=room_type.property, status='confirmed', payment_status='paid',
            check_in=day, check_out=day + timedelta(days=1), number_of_nights=1, guest_count=2,
            total_price=Decimal('60'), number_of_rooms=1, confirmation_code='AAAAA2',
        )
        BookingItem.objects.create(
            booking=confirmed, room_type=room_type, rate_plan=rate_b, number_of_rooms=1,
            price_per_night=Decimal('60'),
        )
        # A cancelled booking must not count.
        cancelled = Booking.objects.create(
            guest=guest, property=room_type.property, status='cancelled', payment_status='refunded',
            check_in=day, check_out=day + timedelta(days=1), number_of_nights=1, guest_count=2,
            total_price=Decimal('60'), number_of_rooms=1, confirmation_code='AAAAA3',
        )
        BookingItem.objects.create(
            booking=cancelled, room_type=room_type, rate_plan=rate_b, number_of_rooms=1,
            price_per_night=Decimal('60'),
        )

        new_apps = self.migrate_forward()
        RoomInventory = new_apps.get_model('properties', 'RoomInventory')
        row = RoomInventory.objects.get(room_type_id=room_type.pk, date=day)
        self.assertEqual(row.booked_rooms, 2)

    def test_is_available_true_when_any_rate_plan_is_open(self):
        apps = self.old_apps
        DateInventory = apps.get_model('properties', 'DateInventory')
        _, room_type, rate_a, rate_b = self._seed_common(apps)
        open_day = timezone.localdate() + timedelta(days=10)
        closed_day = timezone.localdate() + timedelta(days=11)

        DateInventory.objects.create(
            rate_plan=rate_a, date=open_day, available_rooms=1, is_available=False, price=Decimal('70'),
        )
        DateInventory.objects.create(
            rate_plan=rate_b, date=open_day, available_rooms=1, is_available=True, price=Decimal('60'),
        )
        DateInventory.objects.create(
            rate_plan=rate_a, date=closed_day, available_rooms=1, is_available=False, price=Decimal('70'),
        )
        DateInventory.objects.create(
            rate_plan=rate_b, date=closed_day, available_rooms=1, is_available=False, price=Decimal('60'),
        )

        new_apps = self.migrate_forward()
        RoomInventory = new_apps.get_model('properties', 'RoomInventory')
        self.assertTrue(RoomInventory.objects.get(room_type_id=room_type.pk, date=open_day).is_available)
        self.assertFalse(RoomInventory.objects.get(room_type_id=room_type.pk, date=closed_day).is_available)

    def test_oversold_date_is_left_as_computed_not_clamped(self):
        apps = self.old_apps
        DateInventory = apps.get_model('properties', 'DateInventory')
        Booking = apps.get_model('bookings', 'Booking')
        BookingItem = apps.get_model('bookings', 'BookingItem')
        User = apps.get_model('users', 'User')
        owner, room_type, rate_a, rate_b = self._seed_common(apps)
        guest = User.objects.create(email='guest@example.com', password='x')
        day = timezone.localdate() + timedelta(days=10)

        DateInventory.objects.create(rate_plan=rate_a, date=day, available_rooms=1, price=Decimal('70'))
        for i in range(3):
            booking = Booking.objects.create(
                guest=guest, property=room_type.property, status='confirmed', payment_status='paid',
                check_in=day, check_out=day + timedelta(days=1), number_of_nights=1, guest_count=2,
                total_price=Decimal('60'), number_of_rooms=1, confirmation_code=f'BBBBB{i}',
            )
            BookingItem.objects.create(
                booking=booking, room_type=room_type, rate_plan=rate_a, number_of_rooms=1,
                price_per_night=Decimal('60'),
            )

        new_apps = self.migrate_forward()
        RoomInventory = new_apps.get_model('properties', 'RoomInventory')
        row = RoomInventory.objects.get(room_type_id=room_type.pk, date=day)
        # total_rooms=3 caps available at 1 (only rate plan offered 1); 3 bookings held -> oversold
        self.assertEqual(row.available_rooms, 1)
        self.assertEqual(row.booked_rooms, 3)

    def test_date_inventory_rows_are_untouched(self):
        apps = self.old_apps
        DateInventory = apps.get_model('properties', 'DateInventory')
        _, room_type, rate_a, rate_b = self._seed_common(apps)
        day = timezone.localdate() + timedelta(days=10)
        row = DateInventory.objects.create(
            rate_plan=rate_a, date=day, available_rooms=2, booked_rooms=1, price=Decimal('70'),
        )

        self.migrate_forward()

        row.refresh_from_db()
        self.assertEqual(row.available_rooms, 2)
        self.assertEqual(row.booked_rooms, 1)

    def test_reverse_migration_empties_room_inventory(self):
        apps = self.old_apps
        DateInventory = apps.get_model('properties', 'DateInventory')
        _, room_type, rate_a, rate_b = self._seed_common(apps)
        day = timezone.localdate() + timedelta(days=10)
        DateInventory.objects.create(rate_plan=rate_a, date=day, available_rooms=2, price=Decimal('70'))

        new_apps = self.migrate_forward()
        RoomInventory = new_apps.get_model('properties', 'RoomInventory')
        self.assertEqual(RoomInventory.objects.count(), 1)

        executor = self._executor
        executor.loader.build_graph()
        executor.migrate(self.migrate_from)
        executor.loader.build_graph()
        reverted_apps = executor.loader.project_state(self.migrate_from).apps
        RoomInventory = reverted_apps.get_model('properties', 'RoomInventory')
        self.assertEqual(RoomInventory.objects.count(), 0)
