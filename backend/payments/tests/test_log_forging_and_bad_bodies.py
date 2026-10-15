"""
A05-2 / A05-3 / A10-8: what an anonymous caller types cannot forge log lines or cause a 500.

Log lines are one line per event. A newline in the webhook provider name or in the URL path
used to start a new, attacker-written line ("... ERROR - Refund approved ..."). A JSON body
that is not an object (`null`, a list) used to crash the webhook with a traceback.
"""
import logging

import pytest
from django.core.exceptions import BadRequest, SuspiciousOperation

from common.exception_handlers import custom_exception_handler

WEBHOOK = '/api/v1/payments/webhook'


def _lines(caplog):
    return [record.getMessage() for record in caplog.records]


@pytest.mark.django_db
class TestWebhookInput:
    def test_an_unknown_provider_is_a_404_and_cannot_forge_an_error_line(self, client, caplog):
        caplog.set_level(logging.INFO)

        response = client.post(f'{WEBHOOK}/x%0A2026-10-13%20ERROR%20forged/', '{}', content_type='application/json',
                               HTTP_X_SIGNATURE='abc')

        assert response.status_code == 404
        assert not [r for r in caplog.records if r.levelno >= logging.WARNING and 'forged' in r.getMessage()]
        assert all('\n' not in line for line in _lines(caplog))

    @pytest.mark.parametrize('body', ['null', '[1, 2]', '"text"', '5'])
    def test_a_json_body_that_is_not_an_object_is_a_400_without_a_traceback(self, client, caplog, body):
        caplog.set_level(logging.INFO)

        response = client.post(f'{WEBHOOK}/payme/', body, content_type='application/json', HTTP_X_SIGNATURE='abc')

        assert response.status_code == 400
        assert not [record for record in caplog.records if record.exc_info]


@pytest.mark.django_db
class TestRequestLog:
    def test_a_newline_in_the_path_does_not_start_a_new_log_line(self, client, caplog):
        # LOG_LEVEL defaults to WARNING without DEBUG, so the app logger is set explicitly
        caplog.set_level(logging.INFO, logger='tickbron')

        client.get('/api/v1/nothing%0A2026-10-13%20ERROR%20Refund%20approved/')

        lines = [line for line in _lines(caplog) if 'Refund' in line]
        assert lines, 'the request should still be logged'
        assert all('\n' not in line and '\r' not in line for line in lines)


class TestBadRequestsAreNot500:
    @pytest.mark.parametrize('error', [SuspiciousOperation('x'), BadRequest('x')])
    def test_django_bad_request_errors_map_to_400(self, error):
        response = custom_exception_handler(error, {})

        assert response.status_code == 400
