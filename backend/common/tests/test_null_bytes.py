"""A NUL character (%00 in a query string, \\u0000 in a JSON body) is refused with 400 before any view or database sees it.

PostgreSQL cannot store or search for it, so without this check a search box or a text field answers 500.
"""
import json

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def client():
    api = APIClient()
    api.raise_request_exception = False
    return api


class TestQueryString:
    def test_a_nul_in_the_query_is_refused(self):
        response = client().get('/api/v1/properties/search/?search=%00')

        assert response.status_code == 400
        assert response.json()['error']['code'] == 'invalid_input'

    def test_a_nul_hidden_in_a_longer_value_is_refused(self):
        assert client().get('/api/v1/properties/search/?search=hot%00el').status_code == 400

    def test_ordinary_queries_still_work(self):
        assert client().get('/api/v1/properties/search/?search=hotel%20tashkent').status_code == 200


class TestJsonBody:
    def post(self, raw):
        return client().post('/api/v1/auth/login/', data=raw, content_type='application/json')

    def test_an_escaped_nul_in_the_body_is_refused(self):
        assert self.post('{"email": "a\\u0000b@example.com", "password": "x"}').status_code == 400

    def test_a_raw_nul_byte_in_the_body_is_refused(self):
        assert self.post('{"email": "a\x00b@example.com", "password": "x"}').status_code == 400

    def test_a_backslash_followed_by_u0000_as_text_is_not_confused_with_a_nul(self):
        # the JSON text "\\u0000" is a backslash and the letters u0000, not a NUL
        body = json.dumps({'email': 'a\\u0000b@example.com', 'password': 'x'})

        assert self.post(body).status_code != 400 or 'invalid_input' not in self.post(body).content.decode()

    def test_a_normal_body_still_works(self):
        assert self.post(json.dumps({'email': 'nobody@example.com', 'password': 'x'})).status_code == 401
