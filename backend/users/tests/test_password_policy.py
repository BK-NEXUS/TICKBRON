"""
Password policy: at least 8 characters with a letter (any case), a digit and a special character.

Upper/lower case are not required separately, and 8 to 11 characters are allowed (it was 12).
The rule is enforced on every API that sets a password.
"""
import pytest
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from users.models import User
from users.validators import StrongPasswordValidator

REGISTER_URL = '/api/v1/auth/register/'

ACCEPTED = [
    'kitob7#yoz',      # lowercase only, 10 characters
    'KITOB7#YOZ',      # uppercase only
    'sayr5$ol',        # exactly 8 characters
    'sayr5_ol',        # underscore counts as a special character
    'Хорошо7!ok',  # letters of other alphabets count (Cyrillic)
    'bu yol9! ok',     # spaces are allowed inside
]
REJECTED = [
    ('sayr5$o', 'password_too_short'),       # 7 characters
    ('12345678', 'password_no_letter'),      # digits only
    ('!@#$%^&*', 'password_no_letter'),      # specials only
    ('kitobyoz#', 'password_no_digit'),      # no digit
    ('kitobyoz7', 'password_no_special'),    # no special character
    ('kitob7  yoz', 'password_no_special'),  # a space is not a special character
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
