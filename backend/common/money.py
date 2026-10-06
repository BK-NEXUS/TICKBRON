"""
Money rules (R6). The only place that knows which currencies exist and how they round.

- A property is priced in one of SUPPORTED_BASE_CURRENCIES.
- Guests are charged in CHARGE_CURRENCY (Payme and Click only take UZS).
- UZS amounts are whole so'm, USD amounts are cents; both ROUND_HALF_UP.
- Converting a stay to UZS rounds the stay total once, never night by night.
- Decimal only: a float anywhere in money code is a bug, so it raises.
"""
import re
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ImproperlyConfigured

SUPPORTED_BASE_CURRENCIES = ('UZS', 'USD')
CHARGE_CURRENCY = 'UZS'
CURRENCY_CHOICES = [(code, code) for code in SUPPORTED_BASE_CURRENCIES]

_STEP = {'UZS': Decimal('1'), 'USD': Decimal('0.01')}
TIYIN_PER_SOM = 100


def _decimal(value):
    if isinstance(value, float):
        raise TypeError('Money must be Decimal, not float')
    return value if isinstance(value, Decimal) else Decimal(str(value))


def quantize(amount, currency):
    """Round an amount to its currency's smallest unit (UZS whole so'm, USD cents)."""
    if currency not in _STEP:
        raise ValueError(f'Unsupported currency: {currency}')
    return _decimal(amount).quantize(_STEP[currency], rounding=ROUND_HALF_UP)


def to_uzs(amount, rate):
    """Convert an amount to whole so'm at `rate` (so'm per one unit), rounding once."""
    return quantize(_decimal(amount) * _decimal(rate), 'UZS')


def is_whole_som(amount):
    amount = _decimal(amount)
    return amount == amount.to_integral_value()


def som_to_tiyin(amount):
    """Payme works in tiyin (1 so'm = 100 tiyin). Charged amounts are whole so'm."""
    amount = _decimal(amount)
    if not is_whole_som(amount):
        raise ValueError("Charged UZS amounts must be whole so'm")
    return int(amount) * TIYIN_PER_SOM


def tiyin_to_som(value):
    """Provider tiyin (int or digit string) back to so'm as a Decimal."""
    if isinstance(value, bool) or not isinstance(value, (int, str)) or not str(value).isdigit():
        raise ValueError(f'Invalid tiyin amount: {value!r}')
    return Decimal(int(value)) / TIYIN_PER_SOM


def parse_percent(name, raw, default):
    """A percent setting: a whole number 0-100 (None -> default); anything else fails startup."""
    if raw is None:
        return default
    text = str(raw).strip()
    if not re.fullmatch(r'\d{1,3}', text) or int(text) > 100:
        raise ImproperlyConfigured(f'{name} must be a whole number from 0 to 100, got {raw!r}')
    return int(text)
