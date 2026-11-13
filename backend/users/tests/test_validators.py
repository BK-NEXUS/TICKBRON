"""
Paydalanıwshı validatorları ushın testler.
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from users.validators import StrongPasswordValidator, EmailFormatValidator


class TestStrongPasswordValidator(TestCase):
    """StrongPasswordValidator ushın test jaǵdayları."""

    def setUp(self):
        """Test validator ın tayarlaw."""
        self.validator = StrongPasswordValidator(min_length=8)

    def test_valid_strong_password(self):
        """Kúshli paroldi tekseriwdi testlew."""
        password = "StrongP@ssw0rd!X"
        # Hesh qanday exception shıǵarmawı kerek
        self.validator.validate(password)

    def test_password_too_short(self):
        """Júdá qısqa paroldi testlew."""
        password = "Short1!"
        with pytest.raises(ValidationError):
            self.validator.validate(password)

    def test_password_without_uppercase_is_accepted(self):
        """Registr talap etilmeydi: bir túrli hárip jetkilikli."""
        self.validator.validate("lowercase1!@#")

    def test_password_without_lowercase_is_accepted(self):
        """Registr talap etilmeydi: bir túrli hárip jetkilikli."""
        self.validator.validate("UPPERCASE1!@#")

    def test_password_no_letter(self):
        """Hesh bir háripsiz paroldi testlew."""
        with pytest.raises(ValidationError):
            self.validator.validate("1234!@#$")

    def test_password_no_digit(self):
        """Sansız paroldi testlew."""
        password = "NoDigits!@#ABC"
        with pytest.raises(ValidationError):
            self.validator.validate(password)

    def test_password_no_special(self):
        """Arnawlı belgisiz paroldi testlew."""
        password = "NoSpecialChars123ABC"
        with pytest.raises(ValidationError):
            self.validator.validate(password)

    def test_password_common_pattern(self):
        """Keń tarqalǵan úlgili paroldi testlew."""
        password = "Password123!@#"
        with pytest.raises(ValidationError):
            self.validator.validate(password)

    def test_password_sequential_chars(self):
        """Izbe-iz belgili paroldi testlew."""
        password = "abc123!@#ABC"
        with pytest.raises(ValidationError):
            self.validator.validate(password)

    def test_get_help_text(self):
        """Járdem tekstin jaratıwdı testlew."""
        help_text = self.validator.get_help_text()
        assert '8' in help_text
        assert 'letter' in help_text.lower()
        assert 'digit' in help_text.lower()
        assert 'special' in help_text.lower()


class TestEmailFormatValidator(TestCase):
    """EmailFormatValidator ushın test jaǵdayları."""

    def setUp(self):
        """Test validator ın tayarlaw."""
        self.validator = EmailFormatValidator()

    def test_valid_email(self):
        """Jaramlı email di tekseriwdi testlew."""
        email = "user@example.com"
        # Hesh qanday exception shıǵarmawı kerek
        self.validator.validate(email)

    def test_invalid_email_format(self):
        """Jaramsız email formatın testlew."""
        email = "invalid-email"
        with pytest.raises(ValidationError):
            self.validator.validate(email)

    def test_disposable_email(self):
        """Waqtınshalıq email di biykar etiwdi testlew."""
        email = "user@tempmail.com"
        with pytest.raises(ValidationError):
            self.validator.validate(email)

    def test_empty_email(self):
        """Bos email di testlew."""
        email = ""
        with pytest.raises(ValidationError):
            self.validator.validate(email)

    def test_get_help_text(self):
        """Járdem tekstin jaratıwdı testlew."""
        help_text = self.validator.get_help_text()
        assert 'email' in help_text.lower()
        assert 'disposable' in help_text.lower()
