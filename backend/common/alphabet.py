"""
The alphabet filter of the lists of people and hotels: ?letter=A shows only the names that start with A, ?letter=#
the names that do not start with a letter at all (a digit, a quote). One place, so every list does the same.

The name of a person is the one the panels show (full name, else first and last name, else the e-mail address); a
hotel matches when its name in ANY language starts with the letter. Both cases are asked for by hand: a database
with a plain "C" locale does not fold the case of Cyrillic letters by itself.
"""
from django.db.models import CharField, Exists, OuterRef, Q, Value
from django.db.models.functions import Coalesce, Concat, NullIf, Trim
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from properties.models import PropertyTranslation

OTHER = '#'
NOT_A_LETTER = r'^[^[:alpha:]]'

DISPLAY_NAME = Coalesce(
    NullIf('full_name', Value('')),
    NullIf(Trim(Concat('first_name', Value(' '), 'last_name')), Value('')),
    'email',
    output_field=CharField(),
)


def letter_from(request):
    """The wanted letter (upper case) or '#', or None when the request asks for no filter; anything else is a 400."""
    raw = (request.query_params.get('letter') or '').strip()
    if not raw:
        return None
    if raw == OTHER:
        return OTHER
    if len(raw) == 1 and raw.isalpha():
        return raw.upper()
    raise ValidationError({'letter': [_('Use one letter, or # for names that do not start with a letter.')]})


def letter_q(field, letter):
    if letter == OTHER:
        return Q(**{f'{field}__regex': NOT_A_LETTER})
    return Q(**{f'{field}__startswith': letter.upper()}) | Q(**{f'{field}__startswith': letter.lower()})


def people_with_letter(queryset, letter):
    """Users whose shown name starts with `letter` (the queryset is returned as it is for None)."""
    if letter is None:
        return queryset
    return queryset.annotate(alphabet_name=DISPLAY_NAME).filter(letter_q('alphabet_name', letter))


def hotels_with_letter(queryset, letter):
    """Properties with a name, in any language, that starts with `letter`."""
    if letter is None:
        return queryset
    named = PropertyTranslation.objects.filter(property=OuterRef('pk')).filter(letter_q('name', letter))
    return queryset.filter(Exists(named))
