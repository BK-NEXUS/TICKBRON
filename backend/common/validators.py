"""Shared input validators."""
import re

from django.core.exceptions import ValidationError

# Letters and marks of any alphabet, space, hyphen, dot and the apostrophes used in Uzbek names
PERSON_NAME_PATTERN = re.compile(r"^[\w .'ʻʼ’-]*$", re.UNICODE)


def validate_person_name(value):
    """Person names take letters, never digits or symbols."""
    if value and (not PERSON_NAME_PATTERN.match(value) or any(ch.isdigit() or ch == '_' for ch in value)):
        raise ValidationError('Names can contain letters, spaces, hyphens, dots and apostrophes only.')
