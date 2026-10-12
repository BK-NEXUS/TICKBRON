"""
N-13: an anonymous caller must not be able to fill the database through the webhook endpoint.

A request with a bad signature used to store the whole body and an audit row. Now it stores a
fingerprint only, the endpoint is throttled per client IP, and a body larger than any real
provider message is refused before it is parsed into the database.
"""
import json
from unittest import mock

import pytest
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient

from payments.models import PaymentAuditLog, WebhookEvent

URL = '/api/v1/payments/webhook/payme/'
SECRET = {'PAYME_SECRET_KEY': 'webhook-abuse-secret'}


@pytest.fixture
def anonymous():
    return APIClient()


def forged(anonymous, payload=None, signature='forged-signature'):
    payload = payload or {'id': 'evt-forged', 'transaction_id': 'txn-1', 'status': 'completed'}
    with override_settings(**SECRET):
        return anonymous.post(URL, payload, format='json', HTTP_X_SIGNATURE=signature)


@pytest.mark.django_db
class TestBadSignatureStoresAFingerprintOnly:
    def test_the_body_is_not_stored(self, anonymous):
        response = forged(anonymous, {'id': 'evt-forged', 'card_holder': 'Secret Name', 'blob': 'x' * 5000})

        assert response.status_code == 400
        event = WebhookEvent.objects.get(status='invalid_signature')
        assert set(event.payload) == {'redacted', 'sha256'}
        assert event.payload['redacted'] is True
        assert 'Secret Name' not in json.dumps(event.payload)
        assert len(json.dumps(event.payload)) < 200

    def test_the_attacker_supplied_signature_is_not_stored(self, anonymous):
        forged(anonymous, signature='S' * 200)

        event = WebhookEvent.objects.get(status='invalid_signature')
        assert 'S' * 20 not in event.signature

    def test_no_audit_row_is_written_for_a_forged_request(self, anonymous):
        forged(anonymous)

        assert not PaymentAuditLog.objects.filter(action='webhook_received').exists()

    def test_the_same_body_gets_the_same_fingerprint(self, anonymous):
        forged(anonymous)
        forged(anonymous)

        fingerprints = set(WebhookEvent.objects.filter(status='invalid_signature').values_list('payload__sha256', flat=True))
        assert len(fingerprints) == 1

    def test_the_rejection_is_logged_for_monitoring(self, anonymous, caplog):
        with caplog.at_level('WARNING', logger='payments.webhooks'):
            forged(anonymous)

        assert any('Invalid webhook signature' in record.getMessage() for record in caplog.records)


@pytest.mark.django_db
class TestBodySize:
    def test_a_huge_body_is_refused_and_nothing_is_stored(self, anonymous):
        response = forged(anonymous, {'id': 'evt-big', 'blob': 'x' * 200_000})

        assert response.status_code == 400
        assert not WebhookEvent.objects.exists()


@pytest.mark.django_db
class TestThrottle:
    def test_an_ip_that_floods_the_endpoint_is_throttled(self, anonymous):
        from payments.views import WebhookRateThrottle

        cache.clear()
        # DRF reads the rates when the class is defined, so the class attribute is patched
        with mock.patch('payments.views.TESTING', False), \
                mock.patch.object(WebhookRateThrottle, 'THROTTLE_RATES', {'webhook': '3/min'}):
            statuses = [forged(anonymous).status_code for _ in range(5)]

        cache.clear()
        assert statuses[:3] == [400, 400, 400]
        assert 429 in statuses[3:]
