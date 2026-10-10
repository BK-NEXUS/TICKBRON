"""
Tests for login lockout and account enumeration (audit #11).
"""
from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from users import lockout
from users.models import User
from users.services import OTP_INVALID_MESSAGE, OTP_REQUESTED_MESSAGE

LOGIN_URL = '/api/v1/auth/login/'
OTP_REQUEST_URL = '/api/v1/auth/otp/request/'
OTP_VERIFY_URL = '/api/v1/auth/otp/verify/'
PASSWORD = 'correct-password-123'


class LockoutTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='owner@example.com', password=PASSWORD, phone_number='+998901250001',
            phone_verified=True,  # N-1: only a verified number can use SMS login
        )

    def login(self, password, ip, email='owner@example.com'):
        return self.client.post(LOGIN_URL, {'email': email, 'password': password},
                                format='json', REMOTE_ADDR=ip)

    def fail_logins(self, ip, count):
        for _ in range(count):
            self.login('wrong-password', ip)


class TestPerIpLockout(LockoutTestBase):
    """An attacker's failures lock out the attacker's IP, not the account owner."""

    def test_failures_from_one_ip_lock_only_that_ip(self):
        self.fail_logins('203.0.113.66', lockout.IP_FAILURE_LIMIT)

        attacker = self.login(PASSWORD, '203.0.113.66')
        owner = self.login(PASSWORD, '198.51.100.10')

        assert attacker.status_code == 401
        assert owner.status_code == 200

    def test_otp_failures_from_one_ip_do_not_block_the_owner(self):
        for _ in range(lockout.IP_FAILURE_LIMIT):
            self.client.post(OTP_VERIFY_URL, {'phone_number': '+998901250001', 'otp_code': '000000'},
                             format='json', REMOTE_ADDR='203.0.113.66')
        code = self.client.post(OTP_REQUEST_URL, {'phone_number': '+998901250001'},
                                format='json', REMOTE_ADDR='198.51.100.10').data['otp_code']

        owner = self.client.post(OTP_VERIFY_URL, {'phone_number': '+998901250001', 'otp_code': code},
                                 format='json', REMOTE_ADDR='198.51.100.10')

        assert owner.status_code == 200


class TestAccountWideLockout(LockoutTestBase):
    """Distributed guessing from many IPs still locks the account, but later and briefly."""

    def test_many_ips_lock_the_account(self):
        per_ip = lockout.IP_FAILURE_LIMIT - 1  # stay under the per-IP limit
        ips = [f'203.0.113.{i}' for i in range(1, User.ACCOUNT_FAILURE_LIMIT // per_ip + 2)]
        for ip in ips:
            self.fail_logins(ip, per_ip)

        self.user.refresh_from_db()
        assert self.user.is_account_locked()
        assert self.login(PASSWORD, '198.51.100.10').status_code == 401

    def test_account_lock_expires(self):
        User.objects.filter(pk=self.user.pk).update(
            account_locked_until=timezone.now() - timedelta(seconds=1)
        )

        assert self.login(PASSWORD, '198.51.100.10').status_code == 200

    def test_old_failures_do_not_count(self):
        User.objects.filter(pk=self.user.pk).update(
            failed_login_attempts=User.ACCOUNT_FAILURE_LIMIT - 1,
            last_failed_login=timezone.now() - timedelta(minutes=User.ACCOUNT_FAILURE_WINDOW_MINUTES + 1),
        )
        self.user.refresh_from_db()

        self.user.increment_failed_login()

        self.user.refresh_from_db()
        assert self.user.failed_login_attempts == 1
        assert not self.user.is_account_locked()


class TestNoAccountEnumeration(LockoutTestBase):
    """Responses must not reveal whether an email/phone exists or is locked."""

    def test_login_failures_look_identical(self):
        unknown = self.login(PASSWORD, '198.51.100.10', email='nobody@example.com')
        wrong = self.login('wrong-password', '198.51.100.10')
        self.fail_logins('198.51.100.10', lockout.IP_FAILURE_LIMIT)
        locked = self.login(PASSWORD, '198.51.100.10')

        assert unknown.status_code == wrong.status_code == locked.status_code == 401
        assert unknown.data == wrong.data == locked.data

    def test_unknown_email_still_hashes_the_password(self):
        with mock.patch('users.views.make_password') as make_password:
            self.login(PASSWORD, '198.51.100.10', email='nobody@example.com')

        make_password.assert_called_once_with(PASSWORD)

    def test_otp_request_looks_the_same_for_unknown_and_locked_numbers(self):
        unknown = self.client.post(OTP_REQUEST_URL, {'phone_number': '+998909999999'}, format='json')
        self.user.refresh_from_db()
        for _ in range(lockout.IP_FAILURE_LIMIT):
            lockout.record_failure(self.user, '127.0.0.1')
        locked = self.client.post(OTP_REQUEST_URL, {'phone_number': '+998901250001'}, format='json')
        known = self.client.post(OTP_REQUEST_URL, {'phone_number': '+998901250001'},
                                 format='json', REMOTE_ADDR='198.51.100.10')

        assert unknown.status_code == locked.status_code == known.status_code == 200
        assert unknown.data == locked.data == {'success': True, 'message': OTP_REQUESTED_MESSAGE}
        # Registered numbers get the same message; only test mode adds the code
        assert known.data['message'] == OTP_REQUESTED_MESSAGE

    def test_otp_request_without_sms_provider_is_the_same_for_everyone(self):
        with self.settings(SMS_TEST_MODE=False):
            unknown = self.client.post(OTP_REQUEST_URL, {'phone_number': '+998909999999'}, format='json')
            known = self.client.post(OTP_REQUEST_URL, {'phone_number': '+998901250001'}, format='json')

        assert unknown.status_code == known.status_code == 503
        assert unknown.data == known.data

    def test_otp_verify_failures_look_identical(self):
        self.client.post(OTP_REQUEST_URL, {'phone_number': '+998901250001'}, format='json')
        unknown = self.client.post(OTP_VERIFY_URL, {'phone_number': '+998909999999', 'otp_code': '123456'},
                                   format='json')
        wrong = self.client.post(OTP_VERIFY_URL, {'phone_number': '+998901250001', 'otp_code': '000000'},
                                 format='json')
        self.user.refresh_from_db()
        for _ in range(lockout.IP_FAILURE_LIMIT):
            lockout.record_failure(self.user, '127.0.0.1')
        locked = self.client.post(OTP_VERIFY_URL, {'phone_number': '+998901250001', 'otp_code': '000000'},
                                  format='json')

        assert unknown.status_code == wrong.status_code == locked.status_code == 400
        assert unknown.data == wrong.data == locked.data == {'success': False, 'message': OTP_INVALID_MESSAGE}
