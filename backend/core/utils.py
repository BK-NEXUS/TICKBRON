"""
Core utility functions for TICKBRON.

This module contains utility functions used across the application.
"""
import uuid
from django.utils import timezone


def generate_unique_id():
    """
    Generate a unique identifier using UUID4.
    
    Returns:
        str: A unique UUID string
    """
    return str(uuid.uuid4())


def get_current_timestamp():
    """
    Get the current timestamp in UTC.
    
    Returns:
        datetime: Current UTC timestamp
    """
    return timezone.now()


def sanitize_string(input_string, max_length=None):
    """
    Sanitize a string by stripping whitespace and optionally limiting length.
    
    Args:
        input_string: The string to sanitize
        max_length: Maximum length for the string (optional)
    
    Returns:
        str: Sanitized string
    """
    if not input_string:
        return ""
    
    sanitized = input_string.strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_email_format(email):
    """
    Basic email format validation.
    
    Args:
        email: Email address to validate
    
    Returns:
        bool: True if email format appears valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
