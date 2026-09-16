"""
Tests for user validators.
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from users.validators import StrongPasswordValidator, EmailFormatValidator


class TestStrongPasswordValidator(TestCase):
    """Test cases for StrongPasswordValidator."""
    
    def setUp(self):
        """Set up test validator."""
        self.validator = StrongPasswordValidator(min_length=12)
    
    def test_valid_strong_password(self):
        """Test validation of a strong password."""
        password = "StrongP@ssw0rd!X"
        # Should not raise any exception
        self.validator.validate(password)
    
    def test_password_too_short(self):
        """Test password that is too short."""
        password = "Short1!"
        with pytest.raises(ValidationError):
            self.validator.validate(password)
    
    def test_password_no_uppercase(self):
        """Test password without uppercase letter."""
        password = "lowercase1!@#"
        with pytest.raises(ValidationError):
            self.validator.validate(password)
    
    def test_password_no_lowercase(self):
        """Test password without lowercase letter."""
        password = "UPPERCASE1!@#"
        with pytest.raises(ValidationError):
            self.validator.validate(password)
    
    def test_password_no_digit(self):
        """Test password without digit."""
        password = "NoDigits!@#ABC"
        with pytest.raises(ValidationError):
            self.validator.validate(password)
    
    def test_password_no_special(self):
        """Test password without special character."""
        password = "NoSpecialChars123ABC"
        with pytest.raises(ValidationError):
            self.validator.validate(password)
    
    def test_password_common_pattern(self):
        """Test password with common pattern."""
        password = "Password123!@#"
        with pytest.raises(ValidationError):
            self.validator.validate(password)
    
    def test_password_sequential_chars(self):
        """Test password with sequential characters."""
        password = "abc123!@#ABC"
        with pytest.raises(ValidationError):
            self.validator.validate(password)
    
    def test_get_help_text(self):
        """Test help text generation."""
        help_text = self.validator.get_help_text()
        assert '12' in help_text
        assert 'uppercase' in help_text.lower()
        assert 'lowercase' in help_text.lower()
        assert 'digit' in help_text.lower()
        assert 'special' in help_text.lower()


class TestEmailFormatValidator(TestCase):
    """Test cases for EmailFormatValidator."""
    
    def setUp(self):
        """Set up test validator."""
        self.validator = EmailFormatValidator()
    
    def test_valid_email(self):
        """Test validation of valid email."""
        email = "user@example.com"
        # Should not raise any exception
        self.validator.validate(email)
    
    def test_invalid_email_format(self):
        """Test invalid email format."""
        email = "invalid-email"
        with pytest.raises(ValidationError):
            self.validator.validate(email)
    
    def test_disposable_email(self):
        """Test disposable email rejection."""
        email = "user@tempmail.com"
        with pytest.raises(ValidationError):
            self.validator.validate(email)
    
    def test_empty_email(self):
        """Test empty email."""
        email = ""
        with pytest.raises(ValidationError):
            self.validator.validate(email)
    
    def test_get_help_text(self):
        """Test help text generation."""
        help_text = self.validator.get_help_text()
        assert 'email' in help_text.lower()
        assert 'disposable' in help_text.lower()