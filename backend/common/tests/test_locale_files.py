"""The compiled catalogs (.mo) are committed next to their sources (.po); they must be the same."""
from pathlib import Path

import pytest

from scripts.compile_po import compile_po

LOCALE = Path(__file__).resolve().parents[2] / 'locale'


@pytest.mark.parametrize('language', ['uz', 'ru'])
def test_mo_is_the_compiled_po(language):
    folder = LOCALE / language / 'LC_MESSAGES'
    assert (folder / 'django.mo').read_bytes() == compile_po(folder / 'django.po')


@pytest.mark.parametrize('language', ['uz', 'ru'])
def test_every_entry_is_translated(language):
    from scripts.compile_po import read_po
    entries = read_po(LOCALE / language / 'LC_MESSAGES' / 'django.po')
    empty = [msgid for msgid, text in entries.items() if msgid and not text.strip()]
    assert not empty


def test_uzbek_covers_the_drf_texts_the_site_can_show():
    from scripts.compile_po import read_po
    entries = read_po(LOCALE / 'uz' / 'LC_MESSAGES' / 'django.po')
    for msgid in (
        'This field is required.', 'This field may not be blank.', 'A valid integer is required.',
        'Ensure this value is greater than or equal to {min_value}.',
        'Ensure this value is less than or equal to {max_value}.',
        'Ensure this field has no more than {max_length} characters.',
        'Not found.', 'You do not have permission to perform this action.', 'No file was submitted.',
    ):
        assert msgid in entries, msgid


def test_placeholders_survive_translation():
    import re
    from scripts.compile_po import read_po
    for language in ('uz', 'ru'):
        for msgid, text in read_po(LOCALE / language / 'LC_MESSAGES' / 'django.po').items():
            if msgid:
                assert sorted(re.findall(r'\{\w+\}|%\(\w+\)s', msgid)) == sorted(re.findall(r'\{\w+\}|%\(\w+\)s', text)), (language, msgid)
