"""JSON nested too deeply to read is a 400, never a 500 (Python's RecursionError is not a ValueError)."""
import pytest
from rest_framework.test import APIClient

from core.tests.test_r4_permission_matrix import clients  # noqa: F401  (the fixture is reused)

pytestmark = pytest.mark.django_db

PUBLIC_ENDPOINTS = ('/api/v1/auth/login/', '/api/v1/auth/register/')
DEEP_ARRAY = '[' * 20000 + ']' * 20000
DEEP_OBJECT = '{"a":' * 20000 + '1' + '}' * 20000


@pytest.mark.parametrize('path', PUBLIC_ENDPOINTS)
@pytest.mark.parametrize('body', (DEEP_ARRAY, DEEP_OBJECT), ids=('array', 'object'))
def test_json_nested_too_deeply_is_a_client_error(path, body):
    api = APIClient()
    api.raise_request_exception = False

    assert api.post(path, data=body, content_type='application/json').status_code == 400


def test_ordinary_nested_json_still_parses():
    api = APIClient()
    api.raise_request_exception = False

    response = api.post('/api/v1/auth/login/', {'email': 'a@example.com', 'password': 'x', 'extra': {'a': [1, {'b': 2}]}}, format='json')

    assert response.status_code in (400, 401)


def test_the_geography_admin_reads_deep_json_as_a_client_error(clients):  # noqa: F811
    # this view lists its own parsers (it takes pictures), so the default parser does not reach it
    api = clients['superadmin']
    api.raise_request_exception = False

    response = api.post('/api/v1/admin-panel/geography/countries/', data=DEEP_ARRAY, content_type='application/json')

    assert response.status_code == 400
