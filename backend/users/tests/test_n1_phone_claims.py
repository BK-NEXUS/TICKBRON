"""
N-1 stage 2: an unverified phone number is only a claim. It must not block the
real owner, and verifying a number takes it away from every unproven claim.
"""
import pytest
from django.core.cache import cache
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from users.models import User

PHONE = '+998901230777'


def make_user(email, phone=PHONE, verified=False):
    return User.objects.create_user(email=email, password='x-pass-123', phone_number=phone, phone_verified=verified)


class UnverifiedClaimsDoNotBlockTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_two_unverified_claims_can_share_a_number(self):
        make_user('a@example.com')
        make_user('b@example.com')

        self.assertEqual(User.objects.filter(phone_number=PHONE).count(), 2)

    def test_an_unverified_claim_can_sit_next_to_a_verified_owner(self):
        make_user('real@example.com', verified=True)
        make_user('claim@example.com')

        self.assertEqual(User.objects.filter(phone_number=PHONE).count(), 2)

    def test_database_rejects_two_verified_holders(self):
        make_user('a@example.com', verified=True)

        with pytest.raises(IntegrityError), transaction.atomic():
            make_user('b@example.com', verified=True)

    def test_registering_with_a_number_claimed_but_unverified_is_allowed(self):
        make_user('squatter@example.com')

        response = self.client.post('/api/v1/auth/register/', {
            'email': 'owner@example.com', 'full_name': 'Real Owner', 'phone_number': PHONE,
            'password': 'Str0ng#Pass-2026!', 'password_confirm': 'Str0ng#Pass-2026!',
        }, format='json')

        self.assertEqual(response.status_code, 201, response.data)

    def test_registering_with_a_verified_number_is_refused(self):
        make_user('real@example.com', verified=True)

        response = self.client.post('/api/v1/auth/register/', {
            'email': 'other@example.com', 'full_name': 'Other', 'phone_number': PHONE,
            'password': 'Str0ng#Pass-2026!', 'password_confirm': 'Str0ng#Pass-2026!',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('phone_number', response.data)

    def test_profile_update_to_an_unverified_claim_is_allowed(self):
        make_user('squatter@example.com')
        me = make_user('me@example.com', phone='+998901230888')
        self.client.force_authenticate(user=me)

        response = self.client.patch('/api/v1/auth/me/update/', {'phone_number': PHONE}, format='json')

        self.assertEqual(response.status_code, 200, response.data)

    def test_profile_update_to_a_verified_number_is_refused(self):
        make_user('real@example.com', verified=True)
        me = make_user('me@example.com', phone='+998901230888')
        self.client.force_authenticate(user=me)

        response = self.client.patch('/api/v1/auth/me/update/', {'phone_number': PHONE}, format='json')

        self.assertEqual(response.status_code, 400)


class VerifyingClearsOtherClaimsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.squatter = make_user('squatter@example.com')
        self.owner = make_user('owner@example.com')
        self.client.force_authenticate(user=self.owner)

    def _verify(self):
        code = self.client.post('/api/v1/auth/phone/verify/request/', {}, format='json').data['otp_code']
        return self.client.post('/api/v1/auth/phone/verify/confirm/', {'otp_code': code}, format='json')

    def test_the_owner_who_proves_the_number_takes_it_from_the_squatter(self):
        response = self._verify()

        self.assertEqual(response.status_code, 200)
        self.squatter.refresh_from_db()
        self.owner.refresh_from_db()
        self.assertIsNone(self.squatter.phone_number)
        self.assertEqual(self.owner.phone_number, PHONE)
        self.assertTrue(self.owner.phone_verified)

    def test_the_squatter_can_no_longer_ask_for_a_code_for_that_number(self):
        self._verify()
        self.squatter.refresh_from_db()
        self.client.force_authenticate(user=self.squatter)

        response = self.client.post('/api/v1/auth/phone/verify/request/', {}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'phone_missing')

    def test_a_number_verified_elsewhere_in_the_meantime_fails_cleanly(self):
        code = self.client.post('/api/v1/auth/phone/verify/request/', {}, format='json').data['otp_code']
        User.objects.filter(pk=self.squatter.pk).update(phone_verified=True)

        response = self.client.post('/api/v1/auth/phone/verify/confirm/', {'otp_code': code}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'otp_invalid')
        self.owner.refresh_from_db()
        self.assertFalse(self.owner.phone_verified)


class PartialUniqueMigrationTests(TransactionTestCase):
    """Migration 0007 replaces the global unique with 'unique among verified'."""

    before = [('users', '0006_user_phone_number_unique')]
    after = [('users', '0007_phone_number_unique_when_verified')]

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        self._migrate(self.after)

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
