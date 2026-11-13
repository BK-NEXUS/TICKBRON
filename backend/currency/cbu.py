"""
Ózbekstan Orayılıq banki kursın alıw (R6). TEK Celery task
currency.tasks.fetch_exchange_rates hám fetch_exchange_rates management
command ı shaqıradı, hesh qashan paydalanıwshı sorawın islew waqtında emes.

Tekserilgen API (2026-10-03): GET https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/YYYY-MM-DD/
qaytaradı [{"Ccy": "USD", "Code": "840", "Nominal": "1", "Rate": "11772.95",
"Date": "03.10.2026", ...}]: qatarlar, dd.mm.yyyy, sana keleshekte bolsa eń sońǵı járiyalanǵan
kurs. Bir birlik = Rate / Nominal.
"""
import json
import logging
import urllib.request
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import IntegrityError, transaction

from common.dates import business_today
from common.money import CHARGE_CURRENCY, SUPPORTED_BASE_CURRENCIES
from currency.models import ExchangeRate, ExchangeRateFetch

logger = logging.getLogger(__name__)

CBU_URL = 'https://cbu.uz/uz/arkhiv-kursov-valyut/json/{currency}/{day}/'
# Alınatuǵın hár valyutanıń ISO 4217 san kodı (CBU juwabında bolıwı shárt). Valyuta qosıw ushın:
# common.money.CURRENCIES ke, usı jerge hám RATE_SANITY_SHARE ge qosıń.
CBU_CODES = {'USD': '840', 'KZT': '398', 'RUB': '643'}
# FX_MIN_RATE / FX_MAX_RATE bir AQSh dolları ushın jazılǵan; arzanıraq valyuta olardıń óz úlesin aladı
RATE_SANITY_SHARE = {'USD': Decimal('1'), 'KZT': Decimal('0.002'), 'RUB': Decimal('0.01')}
FETCHED_CURRENCIES = tuple(c for c in SUPPORTED_BASE_CURRENCIES if c != CHARGE_CURRENCY)
MAX_BODY_BYTES = 64 * 1024
MAX_RATE_AGE_DAYS = 10


class FetchError(Exception):
    """CBU juwabın paydalanıp bolmadı; sońǵı qabıllanǵan kurs paydalanılıwın dawam etedi."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Hár qanday redirect sátsizlik: kurs belgili CBU URL inen ózinen kelwi kerek."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FetchError(f'redirect {code} refused')


# build_opener ádetdegi HTTPRedirectHandler di usı subclass penen almastıradı
_OPENER = urllib.request.build_opener(_NoRedirect)


def tashkent_today():
    """CBU kurs sanası: is sanası (R12, common.dates.business_today)."""
    return business_today()


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
    except Exception as e:  # URLError, HTTPError, timeout lar, TLS qátelikleri
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
    low = settings.FX_MIN_RATE * RATE_SANITY_SHARE[currency]
    high = settings.FX_MAX_RATE * RATE_SANITY_SHARE[currency]
    if rate < low or rate > high:
        return f'outside the sane range {low}-{high}'
    previous = ExchangeRate.objects.filter(currency=currency, status='accepted').first()
    if previous is not None:
        change = abs(rate - previous.rate) / previous.rate
        if change > settings.FX_MAX_CHANGE:
            return f'change of {change:.1%} from {previous.rate} exceeds {settings.FX_MAX_CHANGE:.0%}'
    return None


def _store(currency, rate, nominal, rate_date):
    """Bir oqılǵan kursı qabıllanǵan yamasa biykar etilgen retinde saqlaw. Qatardı (yamasa bar bolǵanın) qaytaradı."""
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
    except IntegrityError:  # birdey isleniw sol kúndi aldın saqlap qoydı
        return ExchangeRate.objects.get(currency=currency, rate_date=rate_date, source='cbu.uz', status='accepted')
    if reason:
        logger.error(f'CBU {currency} rate {rate} for {rate_date} rejected ({reason}); keeping the previous rate')
    return row


def fetch_and_store(today=None):
    """Hár UZS emes qollap-quwatlanatuǵın valyutanı bir márte alıw. {valyuta: qatar yamasa None} qaytaradı."""
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
