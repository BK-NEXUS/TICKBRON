"""
backend/.env.example sazlamalar oqıytuǵın hár environment ózgeriwshisin dizimleydi, sol sebepli jańa server
koddı oqımastan fayl boyınsha sazlanadı. Ixtıyarıylar komentariyada qalıwı múmkin.
"""
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
SETTINGS_FILES = ['config/settings.py', 'config/logging_config.py']
# Test isleniwiniń ózi oqıydı, operator belgilemeytuǵın nárse
TEST_ONLY = {'PYTEST_CURRENT_TEST', 'TICKBRON_TEST_DB_SUFFIX'}


def _variables_read():
    names = set()
    for relative in SETTINGS_FILES:
        text = (BACKEND_DIR / relative).read_text(encoding='utf-8')
        names |= set(re.findall(r"""os\.(?:getenv|environ\.get)\(\s*['"]([A-Z][A-Z0-9_]*)['"]""", text))
        names |= set(re.findall(r"""parse_\w+\(\s*['"]([A-Z][A-Z0-9_]*)['"]""", text))
    return names - TEST_ONLY


def _variables_listed():
    text = (BACKEND_DIR / '.env.example').read_text(encoding='utf-8')
    return set(re.findall(r'^#?\s*([A-Z][A-Z0-9_]*)=', text, re.MULTILINE))


def test_every_setting_variable_is_in_the_example():
    missing = sorted(_variables_read() - _variables_listed())

    assert not missing, f'add these to backend/.env.example: {missing}'


def test_the_example_lists_no_variable_the_settings_ignore():
    unknown = sorted(_variables_listed() - _variables_read() - {'SECURE_SSL_REDIRECT'})

    assert not unknown, f'no longer read by the settings, remove from backend/.env.example: {unknown}'
