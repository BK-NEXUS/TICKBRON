"""Ortaq kirisiw validator ları."""
import re
import unicodedata

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

# Qálegen alfavitiń háripleri hám belgileri, bos orın, defis, nuqta hám ózbek atlarında paydalanılatuǵın apostroflar
PERSON_NAME_PATTERN = re.compile(r"^[\w .'ʻʼ’-]*$", re.UNICODE)


def validate_person_name(value):
    """Adam atları háripti qabıllaydı, hesh qashan san yamasa belgilerdi emes."""
    if value and (not PERSON_NAME_PATTERN.match(value) or any(ch.isdigit() or ch == '_' for ch in value)):
        raise ValidationError(_('Names can contain letters, spaces, hyphens, dots and apostrophes only.'))


def validate_free_text(value):
    """Mehmanlarǵa kórsetiletuǵın atlar hám táriyplemeler: ápiwayı tekst, markup joq hám basqarıw belgileri joq."""
    if '<' in value or '>' in value:
        raise ValidationError(_('Use plain text without < or >.'))
    if any(unicodedata.category(ch) == 'Cc' and ch not in '\n\r\t' for ch in value):
        raise ValidationError(_('Remove the control characters.'))
