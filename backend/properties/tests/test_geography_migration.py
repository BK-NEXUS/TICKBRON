"""
properties/0013 migration mehmanxanalardıń tekst jaylasıwın Geography ref lerine sáykeslestiredi
(Geography reje G2), hám onıń qaytıwı olardı tazalaydı.

Haqıyqıy migration executor di test database ge qarsı isletedi, sol sebepli sxemanı
alǵa-artqa kóshiredi hám kestelerdi bosatıp baradı. Onı ádettegi suite ten bólek isletiń:

    pytest --create-db properties/tests/test_geography_migration.py
"""
from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class Migrate0012To0013(TransactionTestCase):
    # serialized_rollback joq: aldınǵı TransactionTestCase flush ı content type lerdi jańa
    # kilt ler menen qayta jaratadı, sol sebepli jaratılǵan waqıttaǵı snapshot ti tiklew qaqtıǵısadı. conftest ornına
    # Geografiyanı qayta júkleydi.
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
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        executor.loader.build_graph()
        self.old_apps = executor.loader.project_state(self.migrate_from).apps
        # TransactionTestCase kestelerdi flush etti: sózlikti qayta júkleń (idempotent)
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
        # Region óziniń slug ı (turaqlı kilt) boyınsha tekseriledi: geography 0002 de onıń inglizsha atı
        # ele "Khorezm Region" (0003 keyin qayta ataydı), yamasa flush load_geography di qayta jaratqanda "Khorezm",
        # sol sebepli at usı testten aldın ne islengenine baylanıslı
        self.assertEqual((row.country_ref.code, row.region_ref.slug, row.city_ref.name_en),
                         ('UZ', 'uz-khorezm-region', 'Khiva'))
        # Tekst maydanlar migration tárepinen ózgertilmeydi
        self.assertEqual((row.country, row.state, row.city), ("O'zbekiston", 'Xorazm viloyati', 'Xiva'))
        row = Property.objects.select_related('city_ref').get(pk=tashkent)
        self.assertEqual(row.city_ref.name_en, 'Tashkent')
        row = Property.objects.get(pk=unknown)
        self.assertEqual((row.country_ref_id, row.region_ref_id, row.city_ref_id), (None, None, None))

        old_apps = self._migrate(self.migrate_from)
        Property = old_apps.get_model('properties', 'Property')
        self.assertFalse(Property.objects.filter(country_ref__isnull=False).exists())
        self.assertEqual(Property.objects.get(pk=khiva).city, 'Xiva')
