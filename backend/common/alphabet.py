"""
Adamlar hám mehmanxanalar dizimleriniń alfavit filter i: ?letter=A tek A dan baslanatuǵın atlardı kórsetedi, ?letter=#
hesh qanday háripten baslanbaytuǵın atlardı (san, tırnaq). Bir orın, sol sebepli hár dizim birdey isleydi.

Adamnıń atı panellerde kórsetiletuǵın at (tolıq at, bolmasa atı hám familiyası, bolmasa e-mail mánzil); mehmanxana
qálegen tildegi atı háripten baslansa sáykes keledi. Eki register de qolda soraladı: ápiwayı "C" locale
database Kirill háripleriniń registrin ózi tekseriwdi bilmeydi.
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
    """Kerekli háripti (úlken) yamasa '#', yamasa soraw filter sorawlamasa None; basqa hár nárse 400."""
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
    """Kórsetilgen atı `letter` den baslanatuǵın paydalanıwshılar (None ushın queryset ózgerissiz qaytarıladı)."""
    if letter is None:
        return queryset
    return queryset.annotate(alphabet_name=DISPLAY_NAME).filter(letter_q('alphabet_name', letter))


def hotels_with_letter(queryset, letter):
    """Qálegen tildegi atı `letter` den baslanatuǵın mehmanxanalar."""
    if letter is None:
        return queryset
    named = PropertyTranslation.objects.filter(property=OuterRef('pk')).filter(letter_q('name', letter))
    return queryset.filter(Exists(named))
