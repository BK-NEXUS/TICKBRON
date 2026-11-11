"""
Guards that keep the code base free of the usual ways to open a hole: raw SQL built from text, eval/exec, pickle,
shell calls, switched-off certificate checks and "safe" HTML. They read the source files of the apps (not the tests,
migrations or scripts). A new line that matches fails the test and must be justified or rewritten.
"""
import re
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
SKIPPED_FOLDERS = {'venv', 'node_modules', 'migrations', 'tests', 'scripts', '__pycache__', 'locale', 'static'}

FORBIDDEN = {
    'eval or exec': re.compile(r'(?<![\w.])(eval|exec)\('),
    'pickle': re.compile(r'\bpickle\.loads?\('),
    'unsafe yaml': re.compile(r'\byaml\.load\('),
    'a shell call': re.compile(r'\bos\.system\(|\bsubprocess\.|shell\s*=\s*True'),
    'a switched-off certificate check': re.compile(r'verify\s*=\s*False'),
    'html marked safe': re.compile(r'\bmark_safe\('),
    'raw SQL through the ORM': re.compile(r'\.raw\(|\.extra\(|\bRawSQL\('),
    'SQL built from an f-string': re.compile(r'execute\(\s*f[\'"]'),
}
# The only direct SQL of the project: constant probes of the database connection (no text from outside)
ALLOWED_EXECUTE = re.compile(r"execute\('SELECT (1|version\(\))'\)")
EXECUTE_CALL = re.compile(r'\.execute\(')


def source_files():
    for path in BACKEND.rglob('*.py'):
        if SKIPPED_FOLDERS.isdisjoint(path.relative_to(BACKEND).parts) and path.name != 'conftest.py':
            yield path


def problems_in(text):
    """What is wrong with a piece of source code, as ('kind', line number) pairs."""
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        code = line.split('#', 1)[0]
        for kind, pattern in FORBIDDEN.items():
            if pattern.search(code):
                found.append((kind, number))
        if EXECUTE_CALL.search(code) and not ALLOWED_EXECUTE.search(code):
            found.append(('SQL that is not the constant probe', number))
    return found


@pytest.mark.parametrize('snippet,kind', [
    ("result = eval(user_text)", 'eval or exec'),
    ("data = pickle.loads(blob)", 'pickle'),
    ("requests.get(url, verify=False)", 'a switched-off certificate check'),
    ("return mark_safe(text)", 'html marked safe'),
    ("Booking.objects.raw('select * from bookings where id = %s' % pk)", 'raw SQL through the ORM'),
    ("cursor.execute(f'select * from users where email = {email}')", 'SQL built from an f-string'),
    ("cursor.execute('DELETE FROM users')", 'SQL that is not the constant probe'),
    ("subprocess.run(command, shell=True)", 'a shell call'),
])
def test_the_scanner_recognises_each_kind_of_problem(snippet, kind):
    assert kind in [found for found, _ in problems_in(snippet)]


def test_the_scanner_lets_the_constant_probe_and_comments_through():
    assert problems_in("cursor.execute('SELECT 1')") == []
    assert problems_in("cursor.execute('SELECT version()')") == []
    assert problems_in("x = 1  # never use eval(text) here") == []


def test_the_source_of_the_apps_has_none_of_them():
    offences = [f'{path.relative_to(BACKEND)}:{number} {kind}'
                for path in source_files()
                for kind, number in problems_in(path.read_text(encoding='utf-8'))]
    assert offences == [], '\n'.join(offences)
