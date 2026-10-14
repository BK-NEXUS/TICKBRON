"""
L-1 / N-10: the SMS login code is stored as a keyed hash, not as the code.

A database read (backup, replica, SQL injection elsewhere) used to show every live login code.
The code is still valid for 5 minutes and 3 attempts; only what is stored changes.
"""
import re

import pytest
from django.test import override_settings

from users.models import User
from users.otp import hash_otp


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='otp-hash@example.com', password='x-pass-123', phone_number='+998901110077', phone_verified=True,
    )


@pytest.mark.django_db
class TestOtpIsStoredHashed:
    def test_generate_returns_the_code_and_stores_only_its_hash(self, user):
        code = user.generate_otp()
        user.refresh_from_db()

        assert re.fullmatch(r'\d{6}', code)
        assert user.otp_code == hash_otp(code)
        assert user.otp_code != code
        assert len(user.otp_code) == 64

    def test_the_plain_code_is_nowhere_in_the_users_row(self, user):
        code = user.generate_otp()

        assert not User.objects.filter(otp_code=code).exists()

    def test_the_right_code_verifies_and_is_consumed(self, user):
        code = user.generate_otp()

        assert user.verify_otp(code) is True
        assert user.otp_code is None
        assert user.verify_otp(code) is False

    def test_a_wrong_code_fails_and_counts_an_attempt(self, user):
        code = user.generate_otp()
        wrong = '000000' if code != '000000' else '111111'

        assert user.verify_otp(wrong) is False
        user.refresh_from_db()
        assert user.otp_attempts == 1
        assert user.otp_code == hash_otp(code)

    def test_the_hash_depends_on_the_secret_key(self):
        first = hash_otp('123456')
        with override_settings(SECRET_KEY='another-secret-key-' + 'x' * 40):
            second = hash_otp('123456')

        assert first != second
        assert hash_otp('123456') == first

    def test_the_hash_is_not_a_plain_sha256_of_the_code(self):
        import hashlib

        assert hash_otp('123456') != hashlib.sha256(b'123456').hexdigest()
