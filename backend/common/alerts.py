"""
Telegram alerts for the events somebody should look at now.

A logging handler on the security log and the error logs decides what is worth a message:

- security events listed in ALERT_EVENTS (an account lock, a forged or unappliable payment webhook)
- any ERROR record (a server error, a failed money operation)

The same message is sent once per ALERT_COOLDOWN_SECONDS, so an attack or an error loop produces
one message, not a flood. Sending happens in a Celery task (common/tasks.py), never in the request.
Without TELEGRAM_BOT_TOKEN and TELEGRAM_ALERT_CHAT_ID nothing is sent.
"""
import logging
import re

from django.conf import settings
from django.core.cache import cache

from common.security_log import security_logger

ALERT_EVENTS = frozenset({'lockout', 'webhook_rejected', 'webhook_not_applied'})
ALERT_COOLDOWN_SECONDS = 10 * 60
MAX_ALERT_LENGTH = 500

_EVENT_NAME = re.compile(r'^event=(\w+)')


def alerts_configured():
    return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ALERT_CHAT_ID)


def send_alert(text):
    """Queue a Telegram message unless alerts are off or this exact text was sent recently."""
    if not alerts_configured():
        return
    text = text[:MAX_ALERT_LENGTH]
    if not cache.add(f'alert:{text}', 1, ALERT_COOLDOWN_SECONDS):
        return
    from common.tasks import send_telegram_message
    send_telegram_message.delay(f'TICKBRON alert\n{text}')


def _is_alert_worthy(record):
    """A configured security event, or any record at ERROR level."""
    if record.name == security_logger.name:
        match = _EVENT_NAME.match(record.getMessage())
        return bool(match) and match.group(1) in ALERT_EVENTS
    return record.levelno >= logging.ERROR


class AlertHandler(logging.Handler):
    """Logging handler that turns alert-worthy records into Telegram messages."""

    def emit(self, record):
        try:
            if _is_alert_worthy(record):
                send_alert(record.getMessage())
        except Exception:
            # An alert problem (broker down, cache down) must never break the request being logged
            self.handleError(record)
