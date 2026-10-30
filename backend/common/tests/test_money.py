"""
R6: money rules (common/money.py). UZS is whole so'm, USD is cents, both
ROUND_HALF_UP; conversion to UZS rounds the stay total once; floats are refused.
"""
from decimal import Decimal

import pytest

from common.money import (
    CHARGE_CURRENCY, SUPPORTED_BASE_CURRENCIES, is_valid_unit, quantize, to_uzs,
)


def test_supported_currencies_live_in_one_place():
    assert SUPPORTED_BASE_CURRENCIES == ('UZS', 'USD', 'KZT', 'RUB')
    assert CHARGE_CURRENCY == 'UZS'


@pytest.mark.parametrize('amount, expected', [
    ('2354589.50', '2354590'),
    ('2354589.49', '2354589'),
    ('0.50', '1'),
    ('1250000', '1250000'),
])
def test_uzs_rounds_half_up_to_whole_som(amount, expected):
    result = quantize(Decimal(amount), 'UZS')
    assert result == Decimal(expected)
    assert result.as_tuple().exponent == 0


@pytest.mark.parametrize('amount, expected', [('10.005', '10.01'), ('10.004', '10.00'), ('7', '7.00')])
def test_usd_rounds_half_up_to_cents(amount, expected):
    assert str(quantize(Decimal(amount), 'USD')) == expected


@pytest.mark.parametrize('currency, amount, expected', [
    ('KZT', '45000.5', '45001'), ('KZT', '45000.4', '45000'), ('RUB', '9999.5', '10000'), ('RUB', '100', '100'),
])
def test_tenge_and_ruble_are_whole_units(currency, amount, expected):
    result = quantize(Decimal(amount), currency)
    assert result == Decimal(expected)
    assert result.as_tuple().exponent == 0


@pytest.mark.parametrize('currency, amount, valid', [
    ('USD', '10.01', True), ('USD', '10.001', False), ('UZS', '1250000', True), ('UZS', '1250000.5', False),
    ('KZT', '45000', True), ('KZT', '45000.5', False), ('RUB', '9999', True), ('RUB', '9999.5', False),
])
def test_a_price_has_no_finer_part_than_its_currency_unit(currency, amount, valid):
    assert is_valid_unit(Decimal(amount), currency) is valid


def test_adding_a_currency_is_one_registry_line():
    from common import money
    assert set(money.CURRENCIES) == set(money.SUPPORTED_BASE_CURRENCIES) == set(money._STEP)


def test_floats_and_unknown_currencies_are_refused():
    with pytest.raises(TypeError):
        quantize(10.5, 'USD')
    with pytest.raises(ValueError):
        quantize(Decimal('1'), 'EUR')


def test_conversion_rounds_the_total_once():
    rate = Decimal('11772.95')
    nights = [Decimal('33.33'), Decimal('33.33'), Decimal('33.34')]
    # Rounding each night first gives 392 392 + 392 392 + 392 510 = 1 177 294, one so'm short
    assert sum(to_uzs(n, rate) for n in nights) == Decimal('1177294')
    assert to_uzs(sum(nights), rate) == Decimal('1177295')


def test_to_uzs_example_from_the_plan():
    assert to_uzs(Decimal('200.00'), Decimal('11772.95')) == Decimal('2354590')
