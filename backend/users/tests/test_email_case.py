"""
An e-mail address is the same address whatever its capitals (QA finding F2, .ai/QA_REPORT_2026-10-26.md):
one account per mailbox, and signing in works with the capitals a phone keyboard adds.
"""
from unittest import mock

import pytest
from django.core import mail
from django.core.cache import cache
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from partner.tests.geography_helpers import uzbek_location
from users.models import User
from users.tasks import send_password_reset_email

REGISTER = '/api/v1/auth/register/'
LOGIN = '/api/v1/auth/login/'
RESET = '/api/v1/auth/password-reset/request/'
CREATE_OWNER = '/api/v1/admin-panel/users/create-hotel-owner/'
PASSWORD = 'Str0ng#Passw0rd-2026'


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


def signup(email, **extra):
    body = {'email': email, 'full_name': 'Ali Valiyev', 'password': PASSWORD, 'password_confirm': PASSWORD,
            'phone_number': '+998901234567', **extra}
    return APIClient().post(REGISTER, body, format='json')


def login(email, password=PASSWORD):
    return APIClient().post(LOGIN, {'email': email, 'password': password}, format='json')


@pytest.mark.django_db
class TestRegister:
    def test_the_address_is_stored_in_lower_case(self):
        response = signup('Ali.Valiyev@Mail.COM')
        assert response.status_code == 201, response.data
        assert User.objects.get().email == 'ali.valiyev@mail.com'
        assert response.data['email'] == 'ali.valiyev@mail.com'

    @pytest.mark.parametrize('again', ['ali@mail.com', 'ALI@mail.com', 'Ali@Mail.Com', ' ali@mail.com '])
    def test_the_same_address_in_other_capitals_is_refused(self, again):
        assert signup('ali@mail.com').status_code == 201
        response = signup(again)
        assert response.status_code == 400
        assert 'email' in response.data
        assert User.objects.count() == 1

    def test_the_manager_also_lower_cases(self):
        assert User.objects.create_user(email='Mixed@Case.com', password=PASSWORD).email == 'mixed@case.com'


@pytest.mark.django_db
class TestLogin:
    @pytest.mark.parametrize('typed', ['ali@mail.com', 'Ali@mail.com', 'ALI@MAIL.COM', ' ali@mail.com '])
    def test_any_capitals_sign_in_to_the_account(self, typed):
        signup('ali@mail.com')
        response = login(typed)
        assert response.status_code == 200, response.data
        assert response.data['email'] == 'ali@mail.com'

    def test_an_account_made_with_capitals_signs_in_with_lower_case(self):
        signup('Ali@Mail.com')
        assert login('ali@mail.com').status_code == 200

    def test_a_wrong_password_still_fails(self):
        signup('ali@mail.com')
        assert login('Ali@Mail.com', 'Wrong#Passw0rd-2026').status_code == 401


@pytest.mark.django_db
class TestPasswordReset:
    def test_the_reset_mail_goes_to_the_account_whatever_the_capitals(self):
        signup('ali@mail.com')
        with mock.patch('users.tasks.send_password_reset_email.delay',
                        side_effect=lambda user_id: send_password_reset_email.run(user_id)):
            response = APIClient().post(RESET, {'email': 'ALI@Mail.com'}, format='json')
        assert response.status_code == 200
        assert [m.to for m in mail.outbox] == [['ali@mail.com']]


@pytest.mark.django_db
class TestAdminCreatesAnOwner:
    def test_the_address_is_lower_cased_and_a_second_spelling_is_refused(self):
        admin = User.objects.create_superuser(email='root@example.com', password=PASSWORD)
        api = APIClient()
        api.force_authenticate(user=admin)
        body = {'email': 'Owner@Hotel.com', 'first_name': 'Hotel', 'last_name': 'Owner', 'phone_number': '+998901234567',
                'password': PASSWORD, 'password_confirm': PASSWORD, **uzbek_location('Tashkent')}
        assert api.post(CREATE_OWNER, body, format='json').status_code == 201
        assert User.objects.filter(email='owner@hotel.com').exists()
        again = api.post(CREATE_OWNER, {**body, 'email': 'OWNER@hotel.com'}, format='json')
        assert again.status_code == 400
        assert 'email' in again.data


@pytest.mark.django_db
def test_the_database_itself_refuses_two_spellings():
    User.objects.create_user(email='ali@mail.com', password=PASSWORD)
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.bulk_create([User(email='ALI@mail.com')])


class TestEmailCaseMigration(TransactionTestCase):
    """The migration lower-cases the stored addresses and stops, changing nothing, when two differ only by capitals."""

    before = [('users', '0009_drop_sms_login_columns')]
    after = [('users', '0010_email_case_insensitive')]

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        self._migrate(executor.loader.graph.leaf_nodes('users'))

    def test_stored_addresses_are_lower_cased(self):
        OldUser = self._migrate(self.before).get_model('users', 'User')
        OldUser.objects.create(email='Ali@Mail.COM')
        OldUser.objects.create(email='bobur@mail.com')
        NewUser = self._migrate(self.after).get_model('users', 'User')
        assert sorted(NewUser.objects.values_list('email', flat=True)) == ['ali@mail.com', 'bobur@mail.com']

    def test_it_stops_and_names_the_addresses_that_differ_only_by_capitals(self):
        OldUser = self._migrate(self.before).get_model('users', 'User')
        OldUser.objects.create(email='ali@mail.com')
        OldUser.objects.create(email='ALI@mail.com')
        with pytest.raises(RuntimeError, match='ali@mail.com'):
            self._migrate(self.after)
        assert sorted(OldUser.objects.values_list('email', flat=True)) == ['ALI@mail.com', 'ali@mail.com']
        OldUser.objects.all().delete()
