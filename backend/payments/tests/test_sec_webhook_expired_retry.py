"""
SECURITY_REVIEW M-3: an expired delivery must not occupy the event id of the genuine retry.
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from payments.adapters import SignatureValidationError
from payments.models import WebhookEvent
from payments.webhooks import WebhookProcessor


class TestExpiredWebhookDoesNotBlockRetry(TestCase):
    def setUp(self):
        self.processor = WebhookProcessor('payme')
        patcher = patch.multiple(
            self.processor.adapter, secret_key='test_secret', verify_webhook_signature=lambda *a: True
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _payload(self, age_minutes):
        return {'id': 'event_m3', 'timestamp': int((timezone.now() - timedelta(minutes=age_minutes)).timestamp())}

    def test_expired_delivery_is_rejected_without_storing_the_real_event_id(self):
        with self.assertRaises(SignatureValidationError):
            self.processor.process_webhook(self._payload(age_minutes=10), 'sig')

        assert not WebhookEvent.objects.filter(provider_event_id='event_m3').exists()
        rejected = WebhookEvent.objects.get()
        assert rejected.timestamp_valid is False
        assert rejected.status == 'invalid_signature'

    def test_fresh_retry_of_the_same_event_id_is_processed_after_an_expired_one(self):
        with self.assertRaises(SignatureValidationError):
            self.processor.process_webhook(self._payload(age_minutes=10), 'sig')

        event, is_new = self.processor.process_webhook(self._payload(age_minutes=0), 'sig')

        assert is_new is True
        assert event.provider_event_id == 'event_m3'
        assert event.status == 'processed'
