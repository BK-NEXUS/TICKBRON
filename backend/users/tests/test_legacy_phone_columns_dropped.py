"""
Stage 2 of removing SMS login: the unused columns and the unique-when-verified constraint are
gone (migration 0009). The phone number itself stays as plain legacy data, and the migration
can be reversed.
"""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from users.models import User

DROPPED_COLUMNS = {'phone_verified', 'otp_code', 'otp_expires_at', 'otp_attempts'}
BEFORE = [('users', '0008_otp_code_hashed')]
AFTER = [('users', '0009_drop_sms_login_columns')]


def _columns():
    with connection.cursor() as cursor:
        return {column.name for column in connection.introspection.get_table_description(cursor, 'users')}


@pytest.mark.django_db
class TestModelAndApi:

    def test_the_user_model_has_no_sms_fields(self):
        names = {field.name for field in User._meta.get_fields()}

        assert not DROPPED_COLUMNS & names
        assert 'phone_number' in names

    def test_there_is_no_phone_constraint_any_more(self):
        assert not [c for c in User._meta.constraints if 'phone' in c.name]

    def test_two_accounts_may_hold_the_same_legacy_number(self):
        User.objects.create_user(email='a@example.com', password='x-pass-123', phone_number='+998901230777')
        User.objects.create_user(email='b@example.com', password='x-pass-123', phone_number='+998901230777')

        assert User.objects.filter(phone_number='+998901230777').count() == 2

    def test_the_profile_shows_the_old_number_but_no_verification_flag(self):
        user = User.objects.create_user(email='c@example.com', password='x-pass-123', phone_number='+998901230778')
        client = APIClient()
        client.force_authenticate(user=user)

        data = client.get('/api/v1/auth/me/').data

        assert data['phone_number'] == '+998901230778'
        assert 'phone_verified' not in data


class TestMigration0009(TransactionTestCase):

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        # Leave the schema at the newest users migration for the tests that follow
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes('users'))

    def test_forward_drops_the_columns_and_keeps_the_phone_number(self):
        old_apps = self._migrate(BEFORE)
        OldUser = old_apps.get_model('users', 'User')
        OldUser.objects.create(email='one@example.com', phone_number='+998901230901', phone_verified=True)
        assert DROPPED_COLUMNS <= _columns()

        new_apps = self._migrate(AFTER)

        assert not DROPPED_COLUMNS & _columns()
        assert new_apps.get_model('users', 'User').objects.get(email='one@example.com').phone_number == '+998901230901'

    def test_forward_allows_the_same_number_on_two_accounts(self):
        new_apps = self._migrate(AFTER)
        NewUser = new_apps.get_model('users', 'User')

        NewUser.objects.create(email='one@example.com', phone_number='+998901230902')
        NewUser.objects.create(email='two@example.com', phone_number='+998901230902')

        assert NewUser.objects.filter(phone_number='+998901230902').count() == 2

    def test_backward_brings_the_columns_back_with_safe_defaults(self):
        new_apps = self._migrate(AFTER)
        new_apps.get_model('users', 'User').objects.create(email='three@example.com', phone_number='+998901230903')

        old_apps = self._migrate(BEFORE)

        assert DROPPED_COLUMNS <= _columns()
        restored = old_apps.get_model('users', 'User').objects.get(email='three@example.com')
        assert restored.phone_number == '+998901230903'
        assert restored.phone_verified is False
        assert restored.otp_code is None
        assert restored.otp_attempts == 0
