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

LOGIN_URL = '/api/v1/auth/login/'
PASSWORD = 'correct-password-123'


class LockoutTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='owner@example.com', password=PASSWORD,
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
        with mock.patch('users.views.auth.make_password') as make_password:
            self.login(PASSWORD, '198.51.100.10', email='nobody@example.com')

        make_password.assert_called_once_with(PASSWORD)
