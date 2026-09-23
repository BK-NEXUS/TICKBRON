"""
Tests for phone number uniqueness (phone OTP login looks users up by number).
"""
import pytest
from django.db import connection, IntegrityError
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from users.models import User


class TestPhoneNumberUniqueness(TestCase):
    """Phone numbers must be unique across users."""

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email='owner@example.com', password='testpass123', phone_number='+998901230001'
        )

    def test_database_rejects_duplicate_phone(self):
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='dup@example.com', password='testpass123', phone_number='+998901230001'
            )

    def test_blank_phone_numbers_are_stored_as_null(self):
        first = User.objects.create_user(email='a@example.com', password='testpass123', phone_number='')
        second = User.objects.create_user(email='b@example.com', password='testpass123', phone_number='  ')

        first.refresh_from_db()
        second.refresh_from_db()
        assert first.phone_number is None
        assert second.phone_number is None

    def test_register_with_taken_phone_is_rejected(self):
        response = self.client.post('/api/v1/auth/register/', {
            'email': 'new@example.com',
            'full_name': 'New User',
            'phone_number': ' +998901230001 ',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123'
        }, format='json')

        assert response.status_code == 400
        assert 'phone_number' in response.data
        assert not User.objects.filter(email='new@example.com').exists()

    def test_profile_update_to_taken_phone_is_rejected(self):
        attacker = User.objects.create_user(
            email='attacker@example.com', password='testpass123', phone_number='+998901230002'
        )
        self.client.force_authenticate(user=attacker)

        response = self.client.patch('/api/v1/auth/me/update/', {
            'phone_number': '+998901230001'
        }, format='json')

        assert response.status_code == 400
        attacker.refresh_from_db()
        assert attacker.phone_number == '+998901230002'

    def test_profile_update_keeping_own_phone_is_allowed(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch('/api/v1/auth/me/update/', {
            'phone_number': '+998901230001', 'first_name': 'Owner'
        }, format='json')

        assert response.status_code == 200

    def test_changing_phone_resets_verification(self):
        self.owner.phone_verified = True
        self.owner.save()
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch('/api/v1/auth/me/update/', {
            'phone_number': '+998901230099'
        }, format='json')

        assert response.status_code == 200
        self.owner.refresh_from_db()
        assert self.owner.phone_number == '+998901230099'
        assert self.owner.phone_verified is False


class TestPhoneUniqueMigration(TransactionTestCase):
    """Migration 0006 normalizes blanks and stops on duplicate numbers."""

    before = [('users', '0005_user_preferred_contact_method_user_telegram_and_more')]
    after = [('users', '0006_user_phone_number_unique')]

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        # Leave the schema at the latest migration for the following tests
        self._migrate(self.after)

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
