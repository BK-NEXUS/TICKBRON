"""
N-1: a phone number must be proven by SMS before it can be used to log in.

Without that, anyone could register with a victim's number; the victim's own
SMS login would then land in the attacker's account.
"""
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from users import lockout
from users.models import User

PHONE = '+998901112233'
REQUEST_URL = '/api/v1/auth/otp/request/'
VERIFY_URL = '/api/v1/auth/otp/verify/'
PHONE_REQUEST_URL = '/api/v1/auth/phone/verify/request/'
PHONE_CONFIRM_URL = '/api/v1/auth/phone/verify/confirm/'


class SmsLoginRequiresVerifiedPhoneTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_unverified_number_gets_no_code(self):
        attacker = User.objects.create_user(email='attacker@example.com', password='x-pass-123', phone_number=PHONE)

        response = self.client.post(REQUEST_URL, {'phone_number': PHONE}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('otp_code', response.data)
        attacker.refresh_from_db()
        self.assertIsNone(attacker.otp_code)

    def test_unverified_number_cannot_log_in_even_with_a_valid_code(self):
        attacker = User.objects.create_user(email='attacker@example.com', password='x-pass-123', phone_number=PHONE)
        code = attacker.generate_otp()

        response = self.client.post(VERIFY_URL, {'phone_number': PHONE, 'otp_code': code}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('_auth_user_id', self.client.session)
        attacker.refresh_from_db()
        self.assertFalse(attacker.phone_verified)

    def test_victim_does_not_end_up_in_the_attackers_account(self):
        register = self.client.post('/api/v1/auth/register/', {
            'email': 'attacker@example.com', 'password': 'Str0ng#Pass-2026!', 'password_confirm': 'Str0ng#Pass-2026!',
            'full_name': 'Attacker A', 'phone_number': PHONE,
        }, format='json')
        self.assertEqual(register.status_code, status.HTTP_201_CREATED, register.data)
        victim_browser = self.client_class()

        requested = victim_browser.post(REQUEST_URL, {'phone_number': PHONE}, format='json')

        self.assertNotIn('otp_code', requested.data)
        self.assertNotIn('_auth_user_id', victim_browser.session)

    def test_verified_number_still_logs_in_by_sms(self):
        user = User.objects.create_user(email='real@example.com', password='x-pass-123', phone_number=PHONE)
        User.objects.filter(pk=user.pk).update(phone_verified=True)

        requested = self.client.post(REQUEST_URL, {'phone_number': PHONE}, format='json')
        verified = self.client.post(
            VERIFY_URL, {'phone_number': PHONE, 'otp_code': requested.data['otp_code']}, format='json'
        )

        self.assertEqual(verified.status_code, status.HTTP_200_OK)
        self.assertEqual(verified.data['email'], 'real@example.com')


class PhoneVerificationEndpointsTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(email='me@example.com', password='x-pass-123', phone_number=PHONE)

    def _login(self):
        self.client.force_authenticate(user=self.user)

    def test_endpoints_need_a_session(self):
        self.assertIn(self.client.post(PHONE_REQUEST_URL, {}, format='json').status_code, (401, 403))
        self.assertIn(self.client.post(PHONE_CONFIRM_URL, {'otp_code': '123456'}, format='json').status_code, (401, 403))

    def test_request_sends_a_code_to_the_users_own_number(self):
        self._login()

        response = self.client.post(PHONE_REQUEST_URL, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(response.data['otp_code'], self.user.otp_code)

    def test_request_ignores_a_phone_number_sent_by_the_client(self):
        other = User.objects.create_user(email='other@example.com', password='x-pass-123', phone_number='+998905556677')
        self._login()

        self.client.post(PHONE_REQUEST_URL, {'phone_number': '+998905556677'}, format='json')

        other.refresh_from_db()
        self.assertIsNone(other.otp_code)

    def test_request_without_a_phone_number_is_refused(self):
        User.objects.filter(pk=self.user.pk).update(phone_number=None)
        self.user.refresh_from_db()
        self._login()

        response = self.client.post(PHONE_REQUEST_URL, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'phone_missing')

    def test_request_for_an_already_verified_number_is_refused(self):
        User.objects.filter(pk=self.user.pk).update(phone_verified=True)
        self.user.refresh_from_db()
        self._login()

        response = self.client.post(PHONE_REQUEST_URL, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'phone_already_verified')

    def test_confirm_with_the_right_code_verifies_the_number(self):
        self._login()
        code = self.client.post(PHONE_REQUEST_URL, {}, format='json').data['otp_code']

        response = self.client.post(PHONE_CONFIRM_URL, {'otp_code': code}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['phone_verified'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.phone_verified)

    def test_confirm_with_a_wrong_code_leaves_the_number_unverified(self):
        self._login()
        self.client.post(PHONE_REQUEST_URL, {}, format='json')

        response = self.client.post(PHONE_CONFIRM_URL, {'otp_code': '000000'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.phone_verified)

    def test_confirm_is_refused_while_locked_even_with_the_right_code(self):
        self._login()
        code = self.client.post(PHONE_REQUEST_URL, {}, format='json').data['otp_code']
        for _ in range(lockout.IP_FAILURE_LIMIT):
            lockout.record_failure(self.user, '127.0.0.1')

        response = self.client.post(PHONE_CONFIRM_URL, {'otp_code': code}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.phone_verified)

    def test_profile_exposes_the_verification_state(self):
        self._login()

        before = self.client.get('/api/v1/auth/me/').data
        User.objects.filter(pk=self.user.pk).update(phone_verified=True)
        self.user.refresh_from_db()
        after = self.client.get('/api/v1/auth/me/').data

        self.assertFalse(before['phone_verified'])
        self.assertTrue(after['phone_verified'])
