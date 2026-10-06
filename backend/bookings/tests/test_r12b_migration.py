"""
R12 phase 3: bookings/0010 adds Booking.no_show_refund_percent (existing rows get 0 = nothing
promised) and the NoShowReport table; it reverses cleanly.
"""
from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

BEFORE = [('bookings', '0009_auto_completion_runs')]
AFTER = [('bookings', '0010_r12b_no_show')]


class NoShowMigration(TransactionTestCase):

    def setUp(self):
        super().setUp()
        if connection.vendor != 'postgresql':
            self.skipTest('Migration executor tests need PostgreSQL')
        self.executor = MigrationExecutor(connection)
        self._migrate(BEFORE)

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def _migrate(self, target):
        self.executor.loader.build_graph()
        self.executor.migrate(target)

    def test_old_bookings_promise_nothing_and_the_migration_reverses(self):
        apps = self.executor.loader.project_state(BEFORE).apps
        from properties.models import Property, PropertyType
        from users.models import User
        Booking = apps.get_model('bookings', 'Booking')
        owner = User.objects.create_user(email='o@example.com', password='x')
        hotel = Property.objects.create(
            owner=owner, property_type=PropertyType.objects.create(name='Hotel', slug='hotel'), status='active',
            max_guests=2, bedrooms=1, bathrooms=1, address_line1='1', city='Tashkent', country='Uzbekistan',
            base_price=1, currency='UZS')
        old = Booking.objects.create(
            guest_id=owner.pk, property_id=hotel.pk, status='confirmed', payment_status='paid', check_in='2026-01-10',
            check_out='2026-01-12', number_of_nights=2, guest_count=1, total_price=Decimal('100'), currency='UZS',
            charge_currency='UZS', charge_amount=Decimal('100'), exchange_rate=1, exchange_rate_source='identity',
            confirmation_code='OLD234')

        self._migrate(AFTER)
        with connection.cursor() as cursor:
            assert 'booking_no_show_reports' in connection.introspection.table_names(cursor)
        new_apps = self.executor.loader.project_state(AFTER).apps
        assert new_apps.get_model('bookings', 'Booking').objects.get(pk=old.pk).no_show_refund_percent == 0

        self._migrate(BEFORE)
        with connection.cursor() as cursor:
            assert 'booking_no_show_reports' not in connection.introspection.table_names(cursor)
            columns = [c.name for c in connection.introspection.get_table_description(cursor, 'bookings')]
        assert 'no_show_refund_percent' not in columns
