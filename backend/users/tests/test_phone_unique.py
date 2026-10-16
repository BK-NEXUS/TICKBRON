"""
Tests for the legacy phone number column and its history (migration 0006).
"""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from users.models import User


class TestPhoneNumberStorage(TestCase):
    """A blank number is stored as NULL."""

    def test_blank_phone_numbers_are_stored_as_null(self):
        first = User.objects.create_user(email='a@example.com', password='testpass123', phone_number='')
        second = User.objects.create_user(email='b@example.com', password='testpass123', phone_number='  ')

        first.refresh_from_db()
        second.refresh_from_db()
        assert first.phone_number is None
        assert second.phone_number is None


class TestPhoneUniqueMigration(TransactionTestCase):
    """Migration 0006 normalizes blanks and stops on duplicate numbers."""

    before = [('users', '0005_user_preferred_contact_method_user_telegram_and_more')]
    after = [('users', '0006_user_phone_number_unique')]

    def _latest(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        return executor.loader.graph.leaf_nodes('users')

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        # Leave the schema at the latest migration for the following tests
        self._migrate(self._latest())

    def test_migration_stops_on_duplicate_phone_numbers(self):
        old_apps = self._migrate(self.before)
        OldUser = old_apps.get_model('users', 'User')
        OldUser.objects.create(email='one@example.com', phone_number='+998901230005')
        OldUser.objects.create(email='two@example.com', phone_number=' +998901230005 ')

        with pytest.raises(RuntimeError, match='shared by multiple users'):
            self._migrate(self.after)

        OldUser.objects.all().delete()

    def test_migration_converts_blank_phone_numbers_to_null(self):
        old_apps = self._migrate(self.before)
        OldUser = old_apps.get_model('users', 'User')
        OldUser.objects.create(email='one@example.com', phone_number='')
        OldUser.objects.create(email='two@example.com', phone_number='')

        new_apps = self._migrate(self.after)
        NewUser = new_apps.get_model('users', 'User')

        assert NewUser.objects.filter(phone_number__isnull=True).count() == 2
