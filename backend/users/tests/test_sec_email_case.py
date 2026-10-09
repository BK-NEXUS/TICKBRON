"""
SECURITY_REVIEW M-1: emails are case-insensitive (stored lowercase, unique ignoring case).
"""
import pytest
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from users.models import User

PASSWORD = 'Str0ng!Passw0rd#9'


class TestEmailStoredLowercase(TestCase):
    def test_create_user_lowercases_whole_address(self):
        user = User.objects.create_user(email='  Alice@Example.UZ ', password=PASSWORD)
        assert user.email == 'alice@example.uz'

    def test_plain_save_lowercases_email(self):
        user = User.objects.create(email='Bob@Example.uz')
        user.refresh_from_db()
        assert user.email == 'bob@example.uz'

    def test_database_rejects_case_variant_duplicate(self):
        User.objects.create_user(email='alice@example.uz', password=PASSWORD)
        other = User.objects.create_user(email='other@example.uz', password=PASSWORD)
        with pytest.raises(IntegrityError), transaction.atomic():
            User.objects.filter(pk=other.pk).update(email='ALICE@example.uz')


class TestEmailCaseInEndpoints(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='alice@example.uz', password=PASSWORD)

    def test_login_ignores_email_case(self):
        response = self.client.post(
            '/api/v1/auth/login/', {'email': 'ALICE@Example.UZ', 'password': PASSWORD}, format='json'
        )
        assert response.status_code == 200
        assert response.json()['id'] == self.user.id

    def test_register_with_case_variant_of_existing_email_is_rejected(self):
        response = self.client.post('/api/v1/auth/register/', {
            'email': 'Alice@Example.uz', 'full_name': 'Second Alice', 'phone_number': '+998901230099',
            'password': PASSWORD, 'password_confirm': PASSWORD,
        }, format='json')
        assert response.status_code == 202
        assert User.objects.filter(email__iexact='alice@example.uz').count() == 1
        assert not User.objects.filter(full_name='Second Alice').exists()

    def test_register_stores_lowercase_email(self):
        response = self.client.post('/api/v1/auth/register/', {
            'email': 'Carol@Example.uz', 'full_name': 'Carol', 'phone_number': '+998901230098',
            'password': PASSWORD, 'password_confirm': PASSWORD,
        }, format='json')
        assert response.status_code == 202
        assert User.objects.get(full_name='Carol').email == 'carol@example.uz'

    def test_admin_created_owner_with_case_variant_email_is_rejected(self):
        admin = User.objects.create_superuser(email='root@example.uz', password=PASSWORD)
        self.client.force_authenticate(admin)
        response = self.client.post('/api/v1/admin-panel/users/create-hotel-owner/', {
            'email': 'ALICE@example.uz', 'first_name': 'A', 'last_name': 'B',
            'password': PASSWORD, 'password_confirm': PASSWORD,
        }, format='json')
        assert response.status_code == 400


class TestEmailCaseMigration(TransactionTestCase):
    before = [('users', '0006_user_phone_number_unique')]

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def setUp(self):
        self.latest = [(app, name) for app, name in
                       MigrationExecutor(connection).loader.graph.leaf_nodes() if app == 'users']

    def tearDown(self):
        self._migrate(self.latest)

    def test_migration_stops_on_case_duplicates(self):
        OldUser = self._migrate(self.before).get_model('users', 'User')
        OldUser.objects.create(email='Dup@example.uz')
        OldUser.objects.create(email='dup@example.uz')
        with pytest.raises(RuntimeError, match='differ only by letter case'):
            self._migrate(self.latest)
        OldUser.objects.all().delete()

    def test_migration_lowercases_existing_emails_and_reverses(self):
        OldUser = self._migrate(self.before).get_model('users', 'User')
        OldUser.objects.create(email='Mixed@Example.UZ')
        NewUser = self._migrate(self.latest).get_model('users', 'User')
        assert NewUser.objects.get().email == 'mixed@example.uz'
        OldUser = self._migrate(self.before).get_model('users', 'User')
        assert OldUser.objects.get().email == 'mixed@example.uz'
        OldUser.objects.all().delete()
