"""
Paydalanatuǵın kursı oqıw (R6). Tek database: bul modul hesh qashan tarmaqqa tiymeydi,
sol sebepli soraw handler lerinde qáwipsiz. Kurstıń ózi rejelestirilgen task ta
currency.cbu arqalı alınadı.
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
    """UZS emes mehmanxana ushın ele qabıllanǵan kurs joq: ol UZS de alınıp bolmaydı (R6 A sheshimi)."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = 'exchange_rate_unavailable'
    default_detail = ("This hotel is priced in a foreign currency and today's exchange rate is not available "
                      'yet, so it cannot be booked right now. Please try again later.')


@dataclass(frozen=True)
class RateInfo:
    currency: str
    rate: Decimal            # bir birlikke UZS
    date: Optional[date]
    source: str              # 'cbu.uz' yamasa 'identity'
    stale: bool
    exchange_rate_id: Optional[int] = None

    def as_dict(self):
        return {'rate': f'{self.rate:.6f}', 'date': self.date.isoformat() if self.date else None,
                'source': self.source, 'stale': self.stale}


def current_rate(currency, today=None):
    """
    `currency` di UZS ke házir ótkiziw kursı, yamasa qabıllanǵan kurs ele joq bolsa None.

    UZS ke kurs kerek emes. FX_STALE_AFTER_DAYS tan eski kurs ele qaytarıladı,
    stale=True hám log qa eskertiw menen.
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
    # Saatına hám kurs sanasına eń kóbi bir márte log qa jazıladı (kilt bar waqıtta cache.add ámel emes)
    if stale and cache.add(f'fx-stale-warning:{row.currency}:{row.rate_date}', 1, 3600):
        logger.warning(f'{row.currency} exchange rate of {row.rate_date} is stale (older than '
                       f'{settings.FX_STALE_AFTER_DAYS} days); check the CBU fetch task')
    return RateInfo(row.currency, row.rate, row.rate_date, row.source, stale, row.id)


def current_rates(today=None):
    """
    HÁR qollap-quwatlanatuǵın valyuta ushın {valyuta: RateInfo} BIR query de (R16: bet tórt
    valyutada baha kórsete aladı); qabıllanǵan kursı joq valyuta joq boladı. current_rate penen birdey qaǵıyda.
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
    """`currency` kursı, hár soraw ushın bir márte júklengen barlıq kurslardan (bir query, hesh qashan hár qatar ushın emes)."""
    rates = request.__dict__.get('_tickbron_rates')
    if rates is None:
        rates = request.__dict__['_tickbron_rates'] = current_rates()
    return rates.get(currency)


def uzs_amount(request, amount, currency, key):
    """
    API juwapları ushın `currency` degi `amount` onıń artındaǵı kurs penen somda kórsetilgen:
    {key: "2354590.00" yamasa None, 'exchange_rate': {...} yamasa None}. UZS ke kurs kerek emes
    (exchange_rate None); qabıllanǵan kurs ele joq bolsa ekewi de None.
    """
    from common.money import quantize, to_uzs

    if currency == CHARGE_CURRENCY:
        return {key: f"{quantize(amount, 'UZS'):.2f}", 'exchange_rate': None}
    rate = rate_for_request(request, currency)
    if rate is None:
        return {key: None, 'exchange_rate': None}
    return {key: f'{to_uzs(amount, rate.rate):.2f}', 'exchange_rate': rate.as_dict()}
