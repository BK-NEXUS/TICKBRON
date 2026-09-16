"""
Tests for core utility functions.
"""
import pytest
from core.utils import generate_unique_id, get_current_timestamp, sanitize_string, validate_email_format


class TestCoreUtils:
    """Test cases for core utility functions."""
    
    def test_generate_unique_id(self):
        """Test that generate_unique_id returns a valid UUID."""
        unique_id = generate_unique_id()
        
        assert isinstance(unique_id, str)
        assert len(unique_id) == 36  # UUID4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        
        # Test that multiple calls generate different IDs
        another_id = generate_unique_id()
        assert unique_id != another_id
    
    def test_get_current_timestamp(self):
        """Test that get_current_timestamp returns a valid datetime."""
        from django.utils import timezone
        
        timestamp = get_current_timestamp()
        
        assert isinstance(timestamp, timezone.datetime)
        assert timestamp.tzinfo is not None  # Should be timezone-aware
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        assert sanitize_string("  test  ") == "test"
        assert sanitize_string("") == ""
        assert sanitize_string(None) == ""
    
    def test_sanitize_string_with_max_length(self):
        """Test string sanitization with max length."""
        long_string = "a" * 100
        result = sanitize_string(long_string, max_length=10)
        
        assert len(result) == 10
        assert result == "a" * 10
    
    def test_validate_email_format_valid(self):
        """Test email validation with valid emails."""
        assert validate_email_format("test@example.com") is True
        assert validate_email_format("user.name@domain.co.uk") is True
        assert validate_email_format("user+tag@example.org") is True
    
    def test_validate_email_format_invalid(self):
        """Test email validation with invalid emails."""
        assert validate_email_format("invalid") is False
        assert validate_email_format("invalid@") is False
        assert validate_email_format("@example.com") is False
        assert validate_email_format("test@example") is False
        assert validate_email_format(None) is False
        assert validate_email_format("") is False
