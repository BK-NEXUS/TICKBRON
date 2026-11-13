"""
Parol siyasatı: keminde 8 belgi, háripti (qálegen registr), sandı hám arnawlı belgini óz ishine alıwı kerek.

Úlken/kishi háripler ayrıqsha talap etilmeydi, hám 8 den 11 belgige shekem ruxsat (burın 12 edi).
Qaǵıyda parol qoyatuǵın hár bir API da májbúrlenedi.
"""
import pytest
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from users.models import User
from users.validators import StrongPasswordValidator

REGISTER_URL = '/api/v1/auth/register/'

ACCEPTED = [
    'kitob7#yoz',      # tek kishi háripler, 10 belgi
    'KITOB7#YOZ',      # tek úlken háripler
    'sayr5$ol',        # dál 8 belgi
    'sayr5_ol',        # astı sızıq arnawlı belgi esaplanadı
    'Хорошо7!ok',  # basqa alfavit háripleri esaplanadı (Kirill)
    'bu yol9! ok',     # ishinde bos orınlarǵa ruxsat
]
REJECTED = [
    ('sayr5$o', 'password_too_short'),       # 7 belgi
    ('12345678', 'password_no_letter'),      # tek sanlar
    ('!@#$%^&*', 'password_no_letter'),      # tek arnawlı belgiler
    ('kitobyoz#', 'password_no_digit'),      # san joq
    ('kitobyoz7', 'password_no_special'),    # arnawlı belgi joq
    ('kitob7  yoz', 'password_no_special'),  # bos orın arnawlı belgi emes
    ('Admin7!xy', 'password_common_pattern'),
]


@pytest.mark.parametrize('password', ACCEPTED)
def test_validator_accepts(password):
    StrongPasswordValidator(min_length=8).validate(password)


@pytest.mark.parametrize('password, code', REJECTED)
def test_validator_rejects_with_code(password, code):
    with pytest.raises(ValidationError) as caught:
        StrongPasswordValidator(min_length=8).validate(password)

    assert caught.value.code == code


def test_settings_use_eight_characters():
    assert validate_password('sayr5$ol') is None
    with pytest.raises(ValidationError):
        validate_password('sayr5$o')


def test_help_text_names_the_rules():
    text = StrongPasswordValidator(min_length=8).get_help_text().lower()

    assert '8' in text and 'letter' in text and 'digit' in text and 'special' in text
    assert 'uppercase' not in text and 'lowercase' not in text


def _register(password, n=1):
    return APIClient().post(REGISTER_URL, {
        'email': f'guest{n}@example.com', 'full_name': 'Guest Person',
        'phone_number': f'+99890111{n:04d}', 'password': password, 'password_confirm': password,
    }, format='json')


@pytest.mark.django_db
def test_register_accepts_eight_characters_without_uppercase():
    response = _register('sayr5$ol')

    assert response.status_code == 201
    assert User.objects.get(email='guest1@example.com').check_password('sayr5$ol')


@pytest.mark.django_db
@pytest.mark.parametrize('password', ['sayr5$o', 'kitobyoz7', '12345678'])
def test_register_still_rejects_weak_passwords(password):
    response = _register(password)

    assert response.status_code == 400
    assert 'password' in str(response.data)
