"""
OTP logs must not contain full phone numbers (PII); they carry a masked form.
"""
from django.test import TestCase

from common.privacy import mask_phone
from users.models import User
from users.services import OTPService

PHONE = '+998901234567'
MASKED = mask_phone(PHONE)


class TestMaskPhone(TestCase):
    def test_keeps_prefix_and_last_two_digits(self):
        assert mask_phone('+998901234567') == '+998*******67'

    def test_short_or_empty_values_are_fully_masked(self):
        assert mask_phone('12345') == '***'
        assert mask_phone('') == '***'
        assert mask_phone(None) == '***'


class TestOTPLogsHaveNoPhoneNumber(TestCase):
    def setUp(self):
        self.service = OTPService()
        self.user = User.objects.create_user(
            email='log@example.com', phone_number=PHONE, password='testpass123',
            phone_verified=True,  # N-1: only a verified number can use SMS login
        )

    def assert_masked(self, logs):
        output = '\n'.join(logs.output)
        assert PHONE not in output
        assert MASKED in output

    def test_send_otp_logs_masked_number(self):
        with self.assertLogs('users.services', level='INFO') as logs:
            self.service.send_otp(PHONE)
        self.assert_masked(logs)

    def test_verify_success_logs_masked_number(self):
        code = self.user.generate_otp()
        with self.assertLogs('users.services', level='INFO') as logs:
            result = self.service.verify_otp(PHONE, code)
        assert result['success'] is True
        self.assert_masked(logs)

    def test_verify_failure_logs_masked_number(self):
        self.user.generate_otp()
        with self.assertLogs('users.services', level='INFO') as logs:
            result = self.service.verify_otp(PHONE, '000000')
        assert result['success'] is False
        self.assert_masked(logs)

    def test_verify_unknown_number_logs_masked_number(self):
        unknown = '+998907654321'
        with self.assertLogs('users.services', level='INFO') as logs:
            self.service.verify_otp(unknown, '123456')
        output = '\n'.join(logs.output)
        assert unknown not in output
        assert mask_phone(unknown) in output
