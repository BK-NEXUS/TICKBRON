"""
Reading the rate to use (R6). Database only: this module never touches the network,
so it is safe in request handlers. The rate itself is fetched by currency.cbu in
the scheduled task.
"""
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.conf import settings

from common.money import CHARGE_CURRENCY

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateInfo:
    currency: str
    rate: Decimal            # UZS per one unit
    date: Optional[date]
    source: str              # 'cbu.uz' or 'identity'
    stale: bool
    exchange_rate_id: Optional[int] = None

    def as_dict(self):
        return {'rate': f'{self.rate:.6f}', 'date': self.date.isoformat() if self.date else None,
                'source': self.source, 'stale': self.stale}


def current_rate(currency, today=None):
    """
    The rate to convert `currency` to UZS now, or None when no accepted rate exists yet.

    UZS needs no rate. A rate older than FX_STALE_AFTER_DAYS is still returned, with
    stale=True and a warning in the log.
    """
    from currency.cbu import tashkent_today
    from currency.models import ExchangeRate

    if currency == CHARGE_CURRENCY:
        return RateInfo(currency, Decimal('1'), None, 'identity', False)
    today = today or tashkent_today()
    row = (ExchangeRate.objects.filter(currency=currency, status='accepted', rate_date__lte=today)
           .order_by('-rate_date', '-fetched_at', '-id').first())
    if row is None:
        return None
    stale = row.rate_date < today - timedelta(days=settings.FX_STALE_AFTER_DAYS)
    if stale:
        logger.warning(f'{currency} exchange rate of {row.rate_date} is stale (older than '
                       f'{settings.FX_STALE_AFTER_DAYS} days); check the CBU fetch task')
    return RateInfo(currency, row.rate, row.rate_date, row.source, stale, row.id)


def rate_for_request(request, currency):
    """current_rate() cached on the request: one lookup per request, never per row."""
    cache = request.__dict__.setdefault('_tickbron_rates', {})
    if currency not in cache:
        cache[currency] = current_rate(currency)
    return cache[currency]
