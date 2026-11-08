import logging

import pytest
from django.core.exceptions import ImproperlyConfigured

from common.sms import mask_phone, send_sms

PHONE = '+998901234567'


def test_mask_phone_shows_only_the_last_two_digits():
    assert mask_phone(PHONE) == '*' * 11 + '67'


def test_console_backend_logs_a_masked_number_and_never_the_text(settings, caplog):
    settings.SMS_BACKEND = 'console'
    with caplog.at_level(logging.INFO, logger='common.sms'):
        send_sms(PHONE, 'secret words')
    assert PHONE not in caplog.text
    assert 'secret words' not in caplog.text
    assert '67' in caplog.text


def test_unknown_backend_is_refused(settings):
    settings.SMS_BACKEND = 'something-else'
    with pytest.raises(ImproperlyConfigured):
        send_sms(PHONE, 'hello')