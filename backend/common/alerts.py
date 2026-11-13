"""
Házir birew qarawı kerek waqıyalar ushın Telegram eskertiwleri.

Qáwipsizlik logı hám qátelik log ları boyınsha logging handler xabarǵa ılayıq nárseni sheshedi:

- ALERT_EVENTS tizimindegi qáwipsizlik waqıyaları (akkaunt bloklanıwı)
- qálegen ERROR jazbası (server qátesi)

Birdey xabar ALERT_COOLDOWN_SECONDS ta bir ret jiberiledi, sol sebepli hújim yamasa qátelik sikli
bir xabar beredi, kóp emes. Jiberiw Celery task (common/tasks.py) ishinde boladı, hesh qashan soraw ishinde emes.
TELEGRAM_BOT_TOKEN hám TELEGRAM_ALERT_CHAT_ID bolmasa hesh nárse jiberilmeydi.
"""
import logging
import re

from django.conf import settings
from django.core.cache import cache

from common.security_log import security_logger

ALERT_EVENTS = frozenset({'lockout'})
ALERT_COOLDOWN_SECONDS = 10 * 60
MAX_ALERT_LENGTH = 500

_EVENT_NAME = re.compile(r'^event=(\w+)')


def alerts_configured():
    return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ALERT_CHAT_ID)


def send_alert(text):
    """Eskertiwler óship turmasa yamasa dál sol tekst jaqında jiberilmegen bolsa, Telegram xabarın náwbetke qoyıw."""
    if not alerts_configured():
        return
    text = text[:MAX_ALERT_LENGTH]
    if not cache.add(f'alert:{text}', 1, ALERT_COOLDOWN_SECONDS):
        return
    from common.tasks import send_telegram_message
    send_telegram_message.delay(f'TICKBRON alert\n{text}')


def _is_alert_worthy(record):
    """Sazlanǵan qáwipsizlik waqıyası, yamasa ERROR dárejesindegi qálegen jazba."""
    if record.name == security_logger.name:
        match = _EVENT_NAME.match(record.getMessage())
        return bool(match) and match.group(1) in ALERT_EVENTS
    return record.levelno >= logging.ERROR


class AlertHandler(logging.Handler):
    """Eskertiwge ılayıq jazbalardı Telegram xabarlarına aylandıratuǵın logging handler."""

    def emit(self, record):
        try:
            if _is_alert_worthy(record):
                send_alert(record.getMessage())
        except Exception:
            # Eskertiw máselesi (broker óshken, kesh óshken) log qa jazılıp atırǵan sorawdı hesh qashan buzbawı kerek
            self.handleError(record)
