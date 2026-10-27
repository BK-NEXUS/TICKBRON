"""Shared input validators."""
import re
import unicodedata

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

# Letters and marks of any alphabet, space, hyphen, dot and the apostrophes used in Uzbek names
PERSON_NAME_PATTERN = re.compile(r"^[\w .'ʻʼ’-]*$", re.UNICODE)


def validate_person_name(value):
    """Person names take letters, never digits or symbols."""
    if value and (not PERSON_NAME_PATTERN.match(value) or any(ch.isdigit() or ch == '_' for ch in value)):
        raise ValidationError(_('Names can contain letters, spaces, hyphens, dots and apostrophes only.'))


def validate_free_text(value):
    """Names and descriptions shown to guests: plain text, no markup and no control characters."""
    if '<' in value or '>' in value:
        raise ValidationError(_('Use plain text without < or >.'))
    if any(unicodedata.category(ch) == 'Cc' and ch not in '\n\r\t' for ch in value):
        raise ValidationError(_('Remove the control characters.'))
