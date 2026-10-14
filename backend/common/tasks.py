"""Celery tasks shared by the whole project."""
import json
import logging
import urllib.error
import urllib.request

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = 'https://api.telegram.org/bot{token}/sendMessage'
SEND_TIMEOUT_SECONDS = 5


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def send_telegram_message(self, text):
    """
    Send `text` to the alert chat. Retried twice when Telegram cannot be reached.

    Only the kind of error is logged: the request URL holds the bot token.
    """
    request = urllib.request.Request(
        TELEGRAM_API.format(token=settings.TELEGRAM_BOT_TOKEN),
        data=json.dumps({'chat_id': settings.TELEGRAM_ALERT_CHAT_ID, 'text': text}).encode(),
        headers={'Content-Type': 'application/json'},
    )
    try:
        urllib.request.urlopen(request, timeout=SEND_TIMEOUT_SECONDS).close()
    except (urllib.error.URLError, OSError) as error:
        logger.warning('Telegram alert not delivered: %s', type(error).__name__)
        raise self.retry(exc=error)
