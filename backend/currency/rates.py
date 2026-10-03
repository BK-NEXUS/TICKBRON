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
from django.core.cache import cache
from rest_framework import status
from rest_framework.exceptions import APIException

from common.money import CHARGE_CURRENCY

logger = logging.getLogger(__name__)


class ExchangeRateUnavailable(APIException):
    """No accepted rate yet for a non-UZS property: it cannot be charged in UZS (R6 decision A)."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = 'exchange_rate_unavailable'
    default_detail = ("This hotel is priced in a foreign currency and today's exchange rate is not available "
                      'yet, so it cannot be booked right now. Please try again later.')


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
    # Logged at most once per hour and rate date (cache.add is a no-op while the key exists)
    if stale and cache.add(f'fx-stale-warning:{currency}:{row.rate_date}', 1, 3600):
        logger.warning(f'{currency} exchange rate of {row.rate_date} is stale (older than '
                       f'{settings.FX_STALE_AFTER_DAYS} days); check the CBU fetch task')
    return RateInfo(currency, row.rate, row.rate_date, row.source, stale, row.id)


def rate_for_request(request, currency):
    """current_rate() cached on the request: one lookup per request, never per row."""
    rates = request.__dict__.setdefault('_tickbron_rates', {})
    if currency not in rates:
        rates[currency] = current_rate(currency)
    return rates[currency]


def uzs_amount(request, amount, currency, key):
    """
    `amount` in `currency` shown in so'm with the rate behind it, for API responses:
    {key: "2354590.00" or None, 'exchange_rate': {...} or None}. UZS needs no rate
    (exchange_rate None); no accepted rate yet gives None for both.
    """
    from common.money import quantize, to_uzs

    if currency == CHARGE_CURRENCY:
        return {key: f"{quantize(amount, 'UZS'):.2f}", 'exchange_rate': None}
    rate = rate_for_request(request, currency)
    if rate is None:
        return {key: None, 'exchange_rate': None}
    return {key: f'{to_uzs(amount, rate.rate):.2f}', 'exchange_rate': rate.as_dict()}
