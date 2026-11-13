"""NUL belgisi hesh qashan 500 emes: query string degi %00 aldın biykar etiledi, basqa jerde exception handler 400 menen
juwap beredi.

PostgreSQL onı saqlay da, izley de almaydı, sol sebepli bunsız izlew qutısı yamasa tekserilmegen tekst maydanı 500 beredi.
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
    """Denedegi NUL maydan tekseriwleri yamasa, bolmasa, exception handler tárepinen juwap aladı: hesh qashan 500 emes."""

    def post(self, raw):
        return client().post('/api/v1/auth/login/', data=raw, content_type='application/json')

    def test_an_escaped_nul_in_a_field_is_a_client_error(self):
        assert self.post('{"email": "a\\u0000b@example.com", "password": "x"}').status_code == 400

    def test_a_backslash_followed_by_u0000_as_text_is_an_ordinary_value(self):
        body = json.dumps({'email': 'a\\u0000b@example.com', 'password': 'x'})

        assert self.post(body).status_code < 500

    def test_a_normal_body_still_works(self):
        assert self.post(json.dumps({'email': 'nobody@example.com', 'password': 'x'})).status_code == 401


def test_a_nul_that_reaches_the_database_layer_is_answered_400_not_500():
    from rest_framework.views import exception_handler  # noqa: F401  (the handler is configured in REST_FRAMEWORK)

    from common.exception_handlers import custom_exception_handler

    response = custom_exception_handler(ValueError('A string literal cannot contain NUL (0x00) characters.'), {})

    assert response.status_code == 400
    assert response.data['error']['code'] == 'invalid_input'


def test_any_other_value_error_is_still_a_server_error():
    from common.exception_handlers import custom_exception_handler

    assert custom_exception_handler(ValueError('something else broke'), {}).status_code == 500


class TestCorsHeaders:
    """%00 ushın 400 CORS header lerin alıp júriwi kerek, bolmasa basqa origin degi brauzer 400 ornına CORS qátesin
    kórsetedi."""

    def test_the_refusal_carries_the_cors_headers(self, settings):
        settings.CORS_ALLOWED_ORIGINS = ['http://localhost:3000']

        response = client().get('/api/v1/properties/search/?search=%00', HTTP_ORIGIN='http://localhost:3000')

        assert response.status_code == 400
        assert response['Access-Control-Allow-Origin'] == 'http://localhost:3000'
