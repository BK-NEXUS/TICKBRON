"""
Central Bank of Uzbekistan rate fetch (R6). Called ONLY by the Celery task
currency.tasks.fetch_exchange_rates and the fetch_exchange_rates management
command, never while handling a user request.

Verified API (2026-10-03): GET https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/YYYY-MM-DD/
returns [{"Ccy": "USD", "Code": "840", "Nominal": "1", "Rate": "11772.95",
"Date": "03.10.2026", ...}]: strings, dd.mm.yyyy, latest published rate when the
date is in the future. One unit = Rate / Nominal.
"""
import json
import logging
import urllib.request
import zoneinfo
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from common.money import CHARGE_CURRENCY, SUPPORTED_BASE_CURRENCIES
from currency.models import ExchangeRate, ExchangeRateFetch

logger = logging.getLogger(__name__)

CBU_URL = 'https://cbu.uz/uz/arkhiv-kursov-valyut/json/{currency}/{day}/'
CBU_CODES = {'USD': '840'}
FETCHED_CURRENCIES = tuple(c for c in SUPPORTED_BASE_CURRENCIES if c != CHARGE_CURRENCY)
MAX_BODY_BYTES = 64 * 1024
MAX_RATE_AGE_DAYS = 10
TASHKENT = zoneinfo.ZoneInfo('Asia/Tashkent')


class FetchError(Exception):
    """The CBU answer could not be used; the last accepted rate stays in use."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Any redirect is a failure: the rate must come from the fixed CBU URL itself."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FetchError(f'redirect {code} refused')


# build_opener replaces the default HTTPRedirectHandler with this subclass
_OPENER = urllib.request.build_opener(_NoRedirect)


def tashkent_today():
    return timezone.now().astimezone(TASHKENT).date()


def _download(currency, day):
    url = CBU_URL.format(currency=currency, day=day.isoformat())
    request = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'TICKBRON/1.0'})
    try:
        with _OPENER.open(request, timeout=settings.FX_FETCH_TIMEOUT) as response:
            if response.status != 200:
                raise FetchError(f'HTTP {response.status}')
            if 'json' not in (response.headers.get('Content-Type') or ''):
                raise FetchError('response is not JSON')
            body = response.read(MAX_BODY_BYTES + 1)
    except FetchError:
        raise
    except Exception as e:  # URLError, HTTPError, timeouts, TLS errors
        raise FetchError(f'request failed: {type(e).__name__}')
    if len(body) > MAX_BODY_BYTES:
        raise FetchError('response too large')
    return body


def _parse(body, currency, today):
    try:
        data = json.loads(body)
    except ValueError:
        raise FetchError('invalid JSON')
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise FetchError('expected a list with exactly one rate')
    item = data[0]
    if item.get('Ccy') != currency or item.get('Code') != CBU_CODES[currency]:
        raise FetchError('wrong currency in response')
    try:
        rate = Decimal(str(item['Rate']))
        nominal = int(str(item['Nominal']))
        rate_date = datetime.strptime(str(item['Date']), '%d.%m.%Y').date()
    except (KeyError, InvalidOperation, ValueError):
        raise FetchError('unreadable Rate/Nominal/Date')
    if not rate.is_finite() or rate <= 0 or nominal <= 0:
        raise FetchError('non-positive rate or nominal')
    if rate_date > today:
        raise FetchError('rate date in the future')
    if rate_date < today - timedelta(days=MAX_RATE_AGE_DAYS):
        raise FetchError('rate date too old')
    return (rate / nominal).quantize(Decimal('0.000001')), nominal, rate_date


def _rejection_reason(currency, rate):
    if rate < settings.FX_MIN_RATE or rate > settings.FX_MAX_RATE:
        return f'outside the sane range {settings.FX_MIN_RATE}-{settings.FX_MAX_RATE}'
    previous = ExchangeRate.objects.filter(currency=currency, status='accepted').first()
    if previous is not None:
        change = abs(rate - previous.rate) / previous.rate
        if change > settings.FX_MAX_CHANGE:
            return f'change of {change:.1%} from {previous.rate} exceeds {settings.FX_MAX_CHANGE:.0%}'
    return None


def _store(currency, rate, nominal, rate_date):
    """Save one parsed rate as accepted or rejected. Returns the row (or the existing one)."""
    existing = ExchangeRate.objects.filter(currency=currency, rate_date=rate_date, source='cbu.uz',
                                           status='accepted').first()
    if existing is not None:
        return existing
    reason = _rejection_reason(currency, rate)
    try:
        with transaction.atomic():
            row = ExchangeRate.objects.create(
                currency=currency, rate=rate, nominal=nominal, rate_date=rate_date, source='cbu.uz',
                status='rejected' if reason else 'accepted', note=f'rejected: {reason}' if reason else '',
            )
    except IntegrityError:  # a concurrent run stored the same day first
        return ExchangeRate.objects.get(currency=currency, rate_date=rate_date, source='cbu.uz', status='accepted')
    if reason:
        logger.error(f'CBU {currency} rate {rate} for {rate_date} rejected ({reason}); keeping the previous rate')
    return row


def fetch_and_store(today=None):
    """Fetch every non-UZS supported currency once. Returns {currency: row or None}."""
    today = today or tashkent_today()
    results = {}
    for currency in FETCHED_CURRENCIES:
        try:
            rate, nominal, rate_date = _parse(_download(currency, today), currency, today)
            row = _store(currency, rate, nominal, rate_date)
        except FetchError as e:
            logger.warning(f'CBU {currency} rate fetch failed: {e}; keeping the last accepted rate')
            ExchangeRateFetch.objects.create(currency=currency, success=False, error=str(e)[:255])
            results[currency] = None
            continue
        ExchangeRateFetch.objects.create(
            currency=currency, success=row.status == 'accepted', exchange_rate=row,
            error='' if row.status == 'accepted' else row.note[:255],
        )
        results[currency] = row
    return results
