"""Pútkil proekt ortaq paydalanatuǵın Celery task lar."""
import json
import logging
import urllib.error
import urllib.request

from celery import shared_task
from django.conf import settings
from django.core.management import call_command

logger = logging.getLogger(__name__)

TELEGRAM_API = 'https://api.telegram.org/bot{token}/sendMessage'
SEND_TIMEOUT_SECONDS = 5


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def send_telegram_message(self, text):
    """
    `text` ti eskertiw chatına jiberiw. Telegram ǵa jetip bolmasa eki ret qayta urınıladı.

    Tek qátelik túri log qa jazıladı: soraw URL inde bot token bar.
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


@shared_task
def clear_expired_sessions():
    """Múddeti ótken kirisiw session ların óshiriw: Django olardı database de saqlaydı hám ózi hesh qashan óshirmeydi."""
    call_command('clearsessions')
