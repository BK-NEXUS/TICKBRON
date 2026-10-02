"""
Migration properties/0013 maps the text location of properties to Geography refs
(Geography plan G2), and its reverse clears them.

Runs the real migration executor against the test database, so it migrates the schema
back and forth and truncates tables as it goes. Run it apart from the normal suite:

    pytest --create-db properties/tests/test_geography_migration.py
"""
from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class Migrate0012To0013(TransactionTestCase):
    # No serialized_rollback: an earlier TransactionTestCase flush re-creates content types with new
    # keys, so restoring the creation-time snapshot collides. conftest reloads Geography instead.
    migrate_from = [
        ('properties', '0012_property_geography_refs'),
        ('geography', '0002_initial_data'),
        ('users', '0006_user_phone_number_unique'),
    ]
    migrate_to = [
        ('properties', '0013_map_property_geography'),
        ('geography', '0002_initial_data'),
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
        # TransactionTestCase flushed the tables: load the dictionary again (idempotent)
        from geography.data import load_geography
        load_geography(*(self.old_apps.get_model('geography', name) for name in ('Country', 'Region', 'City')))

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

    def _property(self, apps, country, state, city, n):
        User = apps.get_model('users', 'User')
        PropertyType = apps.get_model('properties', 'PropertyType')
        Property = apps.get_model('properties', 'Property')
        owner, _ = User.objects.get_or_create(email='owner@example.com', defaults={'password': 'x'})
        hotel, _ = PropertyType.objects.get_or_create(slug='hotel', defaults={'name': 'Hotel'})
        return Property.objects.create(
            owner=owner, property_type=hotel, status='active', max_guests=2, address_line1=f'{n} Main St',
            city=city, state=state, country=country, base_price=Decimal('60.00'),
        ).pk

    def test_forward_maps_and_reverse_clears(self):
        khiva = self._property(self.old_apps, "O'zbekiston", 'Xorazm viloyati', 'Xiva', 1)
        tashkent = self._property(self.old_apps, 'Узбекистан', None, 'Ташкент', 2)
        unknown = self._property(self.old_apps, 'Atlantis', None, 'Poseidonia', 3)

        new_apps = self._migrate(self.migrate_to)
        Property = new_apps.get_model('properties', 'Property')

        row = Property.objects.select_related('country_ref', 'region_ref', 'city_ref').get(pk=khiva)
        self.assertEqual((row.country_ref.code, row.region_ref.name_en, row.city_ref.name_en),
                         ('UZ', 'Khorezm Region', 'Khiva'))
        # The text fields are not changed by the migration
        self.assertEqual((row.country, row.state, row.city), ("O'zbekiston", 'Xorazm viloyati', 'Xiva'))
        row = Property.objects.select_related('city_ref').get(pk=tashkent)
        self.assertEqual(row.city_ref.name_en, 'Tashkent')
        row = Property.objects.get(pk=unknown)
        self.assertEqual((row.country_ref_id, row.region_ref_id, row.city_ref_id), (None, None, None))

        old_apps = self._migrate(self.migrate_from)
        Property = old_apps.get_model('properties', 'Property')
        self.assertFalse(Property.objects.filter(country_ref__isnull=False).exists())
        self.assertEqual(Property.objects.get(pk=khiva).city, 'Xiva')
