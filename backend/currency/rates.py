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
    return None if row is None else _rate_info(row, today)


def _rate_info(row, today):
    stale = row.rate_date < today - timedelta(days=settings.FX_STALE_AFTER_DAYS)
    # Logged at most once per hour and rate date (cache.add is a no-op while the key exists)
    if stale and cache.add(f'fx-stale-warning:{row.currency}:{row.rate_date}', 1, 3600):
        logger.warning(f'{row.currency} exchange rate of {row.rate_date} is stale (older than '
                       f'{settings.FX_STALE_AFTER_DAYS} days); check the CBU fetch task')
    return RateInfo(row.currency, row.rate, row.rate_date, row.source, stale, row.id)


def current_rates(today=None):
    """
    {currency: RateInfo} for every supported currency in ONE query (R16: a page can show prices in
    four currencies); a currency without an accepted rate is missing. Same rule as current_rate.
    """
    from common.money import SUPPORTED_BASE_CURRENCIES
    from currency.cbu import tashkent_today
    from currency.models import ExchangeRate

    today = today or tashkent_today()
    rows = (ExchangeRate.objects
            .filter(currency__in=[c for c in SUPPORTED_BASE_CURRENCIES if c != CHARGE_CURRENCY],
                    status='accepted', rate_date__lte=today)
            .order_by('currency', '-rate_date', '-fetched_at', '-id').distinct('currency'))
    rates = {row.currency: _rate_info(row, today) for row in rows}
    rates[CHARGE_CURRENCY] = RateInfo(CHARGE_CURRENCY, Decimal('1'), None, 'identity', False)
    return rates


def rate_for_request(request, currency):
    """The rate of `currency`, from all rates loaded once per request (one query, never per row)."""
    rates = request.__dict__.get('_tickbron_rates')
    if rates is None:
        rates = request.__dict__['_tickbron_rates'] = current_rates()
    return rates.get(currency)


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
