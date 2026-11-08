"""Sending an SMS. The rest of the code only calls send_sms(); which service really sends it is a setting."""
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def mask_phone(phone):
    """Hide all but the last two digits, so a number never shows in full in a log."""
    return '*' * (len(phone) - 2) + phone[-2:]


def _send_console(phone, text):
    # Development and tests: nothing leaves the computer. The text is not logged either, only its length.
    logger.info('SMS (console) to %s, %s characters', mask_phone(phone), len(text))


_BACKENDS = {'console': _send_console}


def send_sms(phone, text):
    try:
        send = _BACKENDS[settings.SMS_BACKEND]
    except KeyError:
        raise ImproperlyConfigured(f'Unknown SMS_BACKEND: {settings.SMS_BACKEND!r}') from None
    send(phone, text)