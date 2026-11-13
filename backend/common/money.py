"""
Pul qaǵıydaları (R6). Qanday valyutalar bar hám qalay jumalaqlanatuǵının biletuǵın birden-bir orın.

- Valyutalardıń birden-bir dizimi tómendegi CURRENCIES: valyuta qosıw ushın sonda bir qatar qosıń (hám onıń
  atın frontend katalogları, `frontend/src/i18n/options.ts` ke); CBU alıw, iyeniń baha qutıları
  hám tekseriw sonnan kelip shıǵadı.
- Mehmanxana SUPPORTED_BASE_CURRENCIES tiń birinde bahalanadı; rate plan hárbirinde óz bahasın alıp júre aladı.
- Mehmanlardan CHARGE_CURRENCY de alınadı (Payme hám Click tek UZS qabıllaydı).
- UZS, KZT hám RUB summaları pútin birlik, USD summaları sent; barlıǵı ROUND_HALF_UP.
- Turıwdı UZS ge ótkiziw turıw jámin bir márte jumalaqlaydı, túnlep emes.
- Tek Decimal: pul kodındaǵı hár float qátelik, sol sebepli kóteriledi.
"""
from decimal import ROUND_HALF_UP, Decimal


# kod -> eń kishi baha birliginiń onlıq belgileri sanı
CURRENCIES = {'UZS': 0, 'USD': 2, 'KZT': 0, 'RUB': 0}
SUPPORTED_BASE_CURRENCIES = tuple(CURRENCIES)
CHARGE_CURRENCY = 'UZS'
CURRENCY_CHOICES = [(code, code) for code in SUPPORTED_BASE_CURRENCIES]

_STEP = {code: Decimal(1).scaleb(-decimals) for code, decimals in CURRENCIES.items()}


def _decimal(value):
    if isinstance(value, float):
        raise TypeError('Money must be Decimal, not float')
    return value if isinstance(value, Decimal) else Decimal(str(value))


def quantize(amount, currency):
    """Summanı óz valyutasınıń eń kishi birligine jumalaqlaw (pútin birlik, yamasa USD ushın sent)."""
    if currency not in _STEP:
        raise ValueError(f'Unsupported currency: {currency}')
    return _decimal(amount).quantize(_STEP[currency], rounding=ROUND_HALF_UP)


def to_uzs(amount, rate):
    """Summanı `rate` (bir birlikke som) boyınsha pútin somǵa ótkiziw, bir márte jumalaqlap."""
    return quantize(_decimal(amount) * _decimal(rate), 'UZS')


def is_valid_unit(amount, currency):
    """`amount` tiń valyutanıń eń kishi birliginen mayda bólegi bolmasa True."""
    return _decimal(amount) == quantize(amount, currency)


def is_whole_som(amount):
    amount = _decimal(amount)
    return amount == amount.to_integral_value()
