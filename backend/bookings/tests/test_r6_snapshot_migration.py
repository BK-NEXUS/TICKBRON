"""
R6 migrations bookings 0006-0008: existing bookings get a 'legacy' charge snapshot in
their own currency, and the Status money totals (grouped per currency) do not move.

Runs the real migration executor against the test database (schema goes back and
forth), like properties/tests/test_room_inventory_migration.py.
"""
from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone

from bookings.stats import metric_totals, revenue_by


def _others_without_bookings_after(graph, bookings_node):
    """Newest node of every other app whose dependencies stop at `bookings_node` or earlier."""
    allowed = set(graph.forwards_plan(bookings_node))
    others = []
    for leaf in graph.leaf_nodes():
        if leaf[0] == 'bookings':
            continue
        node = leaf
        while node is not None and any(
            dep[0] == 'bookings' and dep not in allowed for dep in graph.forwards_plan(node)
        ):
            parents = [p for p in graph.node_map[node].parents if p.key[0] == node[0]]
            node = parents[0].key if parents else None
        if node is not None:
            others.append(node)
    return others


class MigrateBookingSnapshot(TransactionTestCase):
    # No serialized_rollback (see test_room_inventory_migration.py)

    def setUp(self):
        super().setUp()
        if connection.vendor != 'postgresql':
            self.skipTest('Migration executor tests need PostgreSQL')
        executor = MigrationExecutor(connection)
        # Every other app stays on its latest migration that does not need a bookings migration
        # after 0005 (R12: payments/0003 depends on bookings/0009), so the historical models match
        others = _others_without_bookings_after(executor.loader.graph, ('bookings', '0005_status_indexes'))
        self.migrate_from = others + [('bookings', '0005_status_indexes')]
        self.migrate_to = others + [('bookings', '0008_charge_snapshot_required')]
        executor.migrate(self.migrate_from)
        executor.loader.build_graph()
        self.old_apps = executor.loader.project_state(self.migrate_from).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)
        executor.loader.build_graph()
        return executor.loader.project_state(targets).apps

    def _seed(self, apps):
        User = apps.get_model('users', 'User')
        Property = apps.get_model('properties', 'Property')
        PropertyType = apps.get_model('properties', 'PropertyType')
        Booking = apps.get_model('bookings', 'Booking')

        owner = User.objects.create(email='owner@example.com', password='x')
        guest = User.objects.create(email='guest@example.com', password='x')
        kind = PropertyType.objects.create(name='Hotel', slug='hotel')
        usd = Property.objects.create(owner=owner, property_type=kind, status='active', max_guests=2,
                                      address_line1='1', city='Tashkent', country='Uzbekistan',
                                      base_price=Decimal('50'), currency='USD')
        uzs = Property.objects.create(owner=owner, property_type=kind, status='active', max_guests=2,
                                      address_line1='2', city='Samarkand', country='Uzbekistan',
                                      base_price=Decimal('600000'), currency='UZS')
        day = timezone.localdate() - timedelta(days=30)
        rows = [(usd, 'USD', '100.00', 'completed'), (usd, 'USD', '50.50', 'confirmed'),
                (usd, 'EUR', '80.00', 'completed'),        # old demo booking in EUR
                (uzs, 'UZS', '700000.00', 'completed'), (uzs, 'UZS', '1300000.00', 'cancelled')]
        for i, (prop, currency, total, booking_status) in enumerate(rows):
            Booking.objects.create(
                guest=guest, property=prop, status=booking_status, payment_status='paid',
                check_in=day, check_out=day + timedelta(days=1), number_of_nights=1, guest_count=1,
                total_price=Decimal(total), currency=currency, confirmation_code=f'MIG00{i}',
            )

    @staticmethod
    def _status_money(apps):
        counted = apps.get_model('bookings', 'Booking').objects.filter(status__in=['confirmed', 'completed'])
        return metric_totals(counted), revenue_by(counted, 'property_id')

    def test_backfill_and_status_totals_unchanged(self):
        self._seed(self.old_apps)
        before = self._status_money(self.old_apps)

        new_apps = self._migrate(self.migrate_to)

        assert self._status_money(new_apps) == before
        assert before[0]['revenue'] == [
            {'currency': 'EUR', 'amount': '80.00'}, {'currency': 'USD', 'amount': '150.50'},
            {'currency': 'UZS', 'amount': '700000.00'},
        ]
        Booking = new_apps.get_model('bookings', 'Booking')
        for b in Booking.objects.all():
            assert (b.charge_currency, b.charge_amount, b.exchange_rate) == (b.currency, b.total_price, Decimal('1'))
            assert b.exchange_rate_date == b.created_at.date()
            assert b.exchange_rate_source == ('identity' if b.currency == 'UZS' else 'legacy')
            assert b.exchange_rate_stale is False

    def test_reverse_drops_the_snapshot_and_keeps_the_bookings(self):
        self._seed(self.old_apps)
        self._migrate(self.migrate_to)

        old_apps = self._migrate(self.migrate_from)

        Booking = old_apps.get_model('bookings', 'Booking')
        assert Booking.objects.count() == 5
        with connection.cursor() as cursor:
            columns = [c.name for c in connection.introspection.get_table_description(cursor, 'bookings')]
        assert 'charge_amount' not in columns and 'exchange_rate' not in columns
