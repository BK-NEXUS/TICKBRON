"""
Hostile input never produces a 500: every endpoint, every role, bodies and query strings of the wrong shape.

A 500 is a bug even when the caller is malicious: the site says "something broke" instead of the real reason,
and the error log fills up. Wrong input must come back as a 4xx (usually 400) with a message.
"""
import pytest

from core.tests.test_r4_permission_matrix import ENDPOINTS, ROLES, clients  # noqa: F401  (the fixture is reused)

WRITE = ('post', 'put', 'patch')

# Field names the API reads, all set to the same wrong value in one body
FIELDS = (
    'id', 'email', 'name', 'password', 'password_confirm', 'code', 'status', 'comment', 'reason', 'text', 'message', 'title',
    'price', 'price_map', 'base_price', 'amount', 'currency', 'check_in', 'check_out', 'date', 'start_date', 'end_date',
    'from', 'to', 'period', 'property', 'property_id', 'room_type', 'rate_plan', 'photo', 'guests', 'guest_count', 'rooms',
    'latitude', 'longitude', 'country', 'region', 'city', 'language', 'phone_number', 'first_name', 'last_name', 'rating',
    'answer', 'is_active', 'ids', 'items', 'details', 'region_ids', 'translations', 'amenities', 'month', 'year',
)

BAD_VALUES = (
    None, '', 'x' * 5000, '{0} {name} {}', '{', "'; DROP TABLE users; --", '\x00', '<script>alert(1)</script>', '\u0000abc',
    -1, 0, 10 ** 30, -(10 ** 30), 1.5, float('1e308'), True, [], [1, 'a', None], {}, {'a': {'b': [1, {'c': '{x}'}]}},
    '2026-13-45', '0000-00-00', '9999-12-31', '١٢٣',
)

QUERY_STRINGS = (
    '?page=abc', '?page=-1', '?page=99999999999999999999', '?page_size=0', '?page_size=-5', '?page_size=abc',
    '?ordering={', '?ordering=-', '?search=%00', '?search=' + 'a' * 5000, '?from=x&to=y', '?period=zzz', '?year=abc',
    '?status=%27', '?export=zzz', '?id=abc', '?ids=1,a,,', '?date=2026-02-30', '?check_in=2026-13-01&check_out=x',
    '?latitude=abc&longitude=999', '?min_price=abc&max_price=-1', '?language=%00', '?currency=%00%00',
)


def _bodies():
    yield from (value for value in (None, [], 'text', 123, [1, 2, 3], '{', True))
    for value in BAD_VALUES:
        yield {name: value for name in FIELDS}


def _server_errors(client, method, path, bodies):
    client.raise_request_exception = False
    problems = []
    for body in bodies:
        # format='json' needs a JSON-serialisable body; NaN-like floats are sent as plain numbers by the encoder
        try:
            response = getattr(client, method)(path, body, format='json')
        except ValueError:
            continue
        if response.status_code >= 500:
            problems.append((response.status_code, repr(body)[:80]))
    return problems


WRITE_ENDPOINTS = [(m, p) for m, p in ENDPOINTS if m in WRITE]
READ_ENDPOINTS = [(m, p) for m, p in ENDPOINTS if m == 'get']


@pytest.mark.django_db
@pytest.mark.parametrize('method, path', WRITE_ENDPOINTS, ids=[f'{m.upper()} {p}' for m, p in WRITE_ENDPOINTS])
def test_wrong_bodies_never_cause_a_server_error(clients, method, path):  # noqa: F811
    problems = {}
    for role in ROLES:
        found = _server_errors(clients[role], method, path, _bodies())
        if found:
            problems[role] = found[:3]
    assert not problems, problems


@pytest.mark.django_db
@pytest.mark.parametrize('method, path', READ_ENDPOINTS, ids=[f'{m.upper()} {p}' for m, p in READ_ENDPOINTS])
def test_wrong_query_strings_never_cause_a_server_error(clients, method, path):  # noqa: F811
    problems = {}
    for role in ROLES:
        client = clients[role]
        client.raise_request_exception = False
        found = [(response.status_code, query) for query in QUERY_STRINGS
                 for response in [client.get(path + query)] if response.status_code >= 500]
        if found:
            problems[role] = found[:3]
    assert not problems, problems


@pytest.mark.django_db
def test_the_second_step_of_the_login_reads_a_wrong_body_as_nothing(clients):  # noqa: F811
    # the hostile-body test above cannot reach this: the password step has to be done first
    from users import two_factor
    from users.models import User

    user = User.objects.create_user(email='second@example.com', password='Kitob7$yy')
    two_factor.enable(user, two_factor.new_secret(), step=0)
    for body in (None, [], 'text', 123, [1, 2]):
        api = clients['anonymous']
        api.raise_request_exception = False
        api.post('/api/v1/auth/login/', {'email': 'second@example.com', 'password': 'Kitob7$yy'}, format='json')
        assert api.post('/api/v1/auth/login/2fa/', body, format='json').status_code == 401
