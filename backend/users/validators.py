"""
Custom validators for user authentication and security.

This module contains custom validators for password strength, email verification,
and other security-related validations.
"""
import re
import phonenumbers
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

PHONE_NUMBER_ERROR = 'Enter a valid phone number in international format, e.g. +998 90 123 45 67.'

# Spaces, dashes, dots and brackets people type between digit groups
_PHONE_SEPARATORS = re.compile(r'[\s\-.()]')


def parse_phone_number(value):
    """
    Return the E.164 form of a phone number ("+998901234567"), or None if it is
    not a valid number.

    The number must start with "+" and a country code. Separators between
    digit groups are allowed; letters and other characters are not.
    """
    compact = _PHONE_SEPARATORS.sub('', str(value or ''))
    if not re.fullmatch(r'\+\d{1,15}', compact):
        return None
    try:
        number = phonenumbers.parse(compact, None)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(number):
        return None
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def normalize_phone_number(value):
    """E.164 form of a phone number; raises ValidationError if it is not valid."""
    normalized = parse_phone_number(value)
    if normalized is None:
        raise ValidationError(PHONE_NUMBER_ERROR, code='invalid_phone_number')
    return normalized


class StrongPasswordValidator:
    """
    Custom password validator for strong password requirements.
    
    Enforces:
    - Minimum length of 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - No common patterns or sequences
    """
    
    def __init__(self, min_length=12, forbid_sequences=True):
        self.min_length = min_length
        # Off in AUTH_PASSWORD_VALIDATORS: any "abc"/"456" run would also reject
        # long random passphrases, and length + blocklist matter more
        self.forbid_sequences = forbid_sequences
    
    def validate(self, password, user=None):
        """
        Validate password strength.
        """
        if len(password) < self.min_length:
            raise ValidationError(
                _("Password must be at least %(min_length)d characters long."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code='password_no_digit',
            )
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Password must contain at least one special character."),
                code='password_no_special',
            )
        
        # Check for common patterns
        common_patterns = [
            r'123456', r'qwerty', r'password', r'admin', r'letmein',
            r'welcome', r'monkey', r'football', r'abc123', r'111111'
        ]
        
        password_lower = password.lower()
        for pattern in common_patterns:
            if pattern in password_lower:
                raise ValidationError(
                    _("Password contains common patterns and is not secure."),
                    code='password_common_pattern',
                )
        
        # Check for sequential characters
        if self.forbid_sequences and self._has_sequential_chars(password):
            raise ValidationError(
                _("Password contains sequential characters and is not secure."),
                code='password_sequential',
            )
    
    def _has_sequential_chars(self, password):
        """Check if password contains sequential characters."""
        password_lower = password.lower()
        for i in range(len(password_lower) - 2):
            if (ord(password_lower[i+1]) == ord(password_lower[i]) + 1 and
                ord(password_lower[i+2]) == ord(password_lower[i]) + 2):
                return True
        return False
    
    def get_help_text(self):
        """
        Return help text for password requirements.
        """
        return _(
            "Your password must be at least %(min_length)d characters long, "
            "contain at least one uppercase letter, one lowercase letter, "
            "one digit, and one special character. "
            "Avoid common patterns and sequential characters."
        ) % {'min_length': self.min_length}


class EmailFormatValidator:
    """
    Enhanced email format validator.
    
    Validates email format with stricter rules than Django's default.
    """
    
    def validate(self, email):
        """
        Validate email format.
        """
        if not email:
            raise ValidationError(_("Email address is required."))
        
        # Basic format check
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(_("Invalid email format."))
        
        # Check for disposable email domains (basic list)
        disposable_domains = [
            'tempmail.com', 'throwaway.com', 'guerrillamail.com',
            'mailinator.com', '10minutemail.com'
        ]
        
        domain = email.split('@')[1].lower()
        if any(disposable in domain for disposable in disposable_domains):
            raise ValidationError(
                _("Disposable email addresses are not allowed."),
                code='disposable_email',
            )
    
    def get_help_text(self):
        """
        Return help text for email requirements.
        """
        return _("Enter a valid email address. Disposable email addresses are not allowed.")