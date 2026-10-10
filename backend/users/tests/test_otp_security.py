"""
Security tests for phone OTP login: code generation, lockout and throttling.
"""
from unittest import mock

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from users.models import User

REQUEST_URL = '/api/v1/auth/otp/request/'
VERIFY_URL = '/api/v1/auth/otp/verify/'


class OTPTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.phone_number = '+998901240001'
        self.user = User.objects.create_user(
            email='otp@example.com', password='testpass123', phone_number=self.phone_number,
            phone_verified=True,  # N-1: only a verified number can use SMS login
        )

    def request_code(self, phone_number=None):
        return self.client.post(REQUEST_URL, {'phone_number': phone_number or self.phone_number}, format='json')

    def verify(self, code, phone_number=None):
        return self.client.post(VERIFY_URL, {
            'phone_number': phone_number or self.phone_number, 'otp_code': code
        }, format='json')

    def wrong_code(self):
        self.user.refresh_from_db()
        return '000000' if self.user.otp_code != '000000' else '111111'


class TestOTPGeneration(OTPTestBase):
    def test_code_comes_from_secrets(self):
        with mock.patch('secrets.randbelow', return_value=42) as randbelow:
            code = self.user.generate_otp()

        randbelow.assert_called_once_with(10**6)
        assert code == '000042'

    def test_code_does_not_use_random_module(self):
        with mock.patch('random.randint', side_effect=AssertionError('random used')):
            code = self.user.generate_otp()

        assert len(code) == 6 and code.isdigit()

    def test_code_is_not_logged(self):
        with self.assertLogs('users.services', level='INFO') as logs:
            response = self.request_code()

        code = response.data['otp_code']
        assert all(code not in line for line in logs.output)


class TestOTPLockout(OTPTestBase):
    CLIENT_IP = '127.0.0.1'  # APIClient's REMOTE_ADDR

    def lock_for_client_ip(self):
        from users import lockout

        self.user.refresh_from_db()
        for _ in range(lockout.IP_FAILURE_LIMIT):
            lockout.record_failure(self.user, self.CLIENT_IP)

    def test_locked_account_rejects_correct_code_without_consuming_it(self):
        code = self.request_code().data['otp_code']
        self.lock_for_client_ip()

        response = self.verify(code)

        # Same response as a wrong code: the lock is not revealed
        assert response.status_code == 400
        assert response.data['message'] == 'Invalid or expired OTP code'
        self.user.refresh_from_db()
        assert self.user.otp_code == code
        assert self.user.otp_attempts == 0
        # N-1: the fixture user is verified from the start; a refused request must leave that unchanged
        assert self.user.phone_verified is True
        assert '_auth_user_id' not in self.client.session

    def test_locked_account_gets_no_new_code(self):
        self.lock_for_client_ip()

        response = self.request_code()

        # Same response as an unknown number: the lock is not revealed
        assert response.status_code == 200
        assert 'otp_code' not in response.data
        self.user.refresh_from_db()
        assert self.user.otp_code is None

    def test_requesting_new_code_does_not_reset_failed_attempts(self):
        """Five wrong guesses spread over several codes still lock this client out."""
        from users import lockout

        for _ in range(2):
            self.request_code()
            self.verify(self.wrong_code())
            self.verify(self.wrong_code())
        code = self.request_code().data['otp_code']
        self.verify(self.wrong_code())

        self.user.refresh_from_db()
        assert self.user.failed_login_attempts == 5
        assert lockout.is_locked(self.user, self.CLIENT_IP)
        assert self.verify(code).status_code == 400

    def test_successful_login_resets_failed_attempts(self):
        self.request_code()
        self.verify(self.wrong_code())
        code = self.request_code().data['otp_code']

        response = self.verify(code)

        assert response.status_code == 200
        self.user.refresh_from_db()
        assert self.user.failed_login_attempts == 0


@mock.patch('users.views.TESTING', False)
class TestOTPThrottling(OTPTestBase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_verify_is_throttled_per_phone_number(self):
        responses = [self.verify('000000') for _ in range(6)]

        assert all(r.status_code != 429 for r in responses[:5])
        assert responses[5].status_code == 429

    def test_request_throttle_ignores_whitespace_variants(self):
        variants = [self.phone_number, f' {self.phone_number}', f'{self.phone_number}  ', f'\t{self.phone_number} ']

        responses = [self.request_code(phone) for phone in variants]

        assert all(r.status_code == 200 for r in responses[:3])
        assert responses[3].status_code == 429

    def test_verify_throttle_ignores_whitespace_variants(self):
        variants = [self.phone_number, f' {self.phone_number}', f'{self.phone_number} ']

        responses = [self.verify('000000', phone) for phone in variants * 2]

        assert responses[5].status_code == 429
