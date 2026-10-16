"""
History of migration 0007 (unique only for verified numbers). The constraint itself was dropped
by migration 0009; these tests run the old migrations forward and back.
"""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class PartialUniqueMigrationTests(TransactionTestCase):
    """Migration 0007 replaces the global unique with 'unique among verified'."""

    before = [('users', '0006_user_phone_number_unique')]
    after = [('users', '0007_phone_number_unique_when_verified')]

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def _latest(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        return executor.loader.graph.leaf_nodes('users')

    def tearDown(self):
        # Back to the newest users migration, whatever it is, so later tests see the full schema
        self._migrate(self._latest())

    def test_forward_keeps_existing_numbers_and_allows_unverified_duplicates(self):
        old_apps = self._migrate(self.before)
        OldUser = old_apps.get_model('users', 'User')
        OldUser.objects.create(email='one@example.com', phone_number='+998901230901', phone_verified=True)

        new_apps = self._migrate(self.after)
        NewUser = new_apps.get_model('users', 'User')
        NewUser.objects.create(email='two@example.com', phone_number='+998901230902')
        NewUser.objects.create(email='three@example.com', phone_number='+998901230902')

        self.assertEqual(NewUser.objects.filter(phone_number='+998901230901', phone_verified=True).count(), 1)
        self.assertEqual(NewUser.objects.filter(phone_number='+998901230902').count(), 2)

    def test_backward_clears_unverified_duplicates_so_the_global_unique_can_return(self):
        new_apps = self._migrate(self.after)
        NewUser = new_apps.get_model('users', 'User')
        NewUser.objects.create(email='real@example.com', phone_number='+998901230903', phone_verified=True)
        NewUser.objects.create(email='claim@example.com', phone_number='+998901230903')

        old_apps = self._migrate(self.before)
        OldUser = old_apps.get_model('users', 'User')

        self.assertEqual(OldUser.objects.get(email='real@example.com').phone_number, '+998901230903')
        self.assertIsNone(OldUser.objects.get(email='claim@example.com').phone_number)
