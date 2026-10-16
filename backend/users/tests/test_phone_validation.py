"""
Server-side phone number validation: every endpoint that takes a phone number
accepts only a valid international number and stores it as E.164.
"""
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from users.models import User

INVALID_NUMBERS = [
    '+99890123456',     # one digit short
    '+9989012345678',   # one digit too many
    '901234567',        # no country code
    '+998 90 ABC 45 67',
    '+1234567890',      # right shape, but not a real number
    '+' + '9' * 30,     # longer than the column
]
PHONE_ERROR = 'Enter a valid phone number in international format, e.g. +998 90 123 45 67.'


def error_text(response, field='phone_number', errors=None):
    errors = response.data if errors is None else errors
    return ' '.join(str(message) for message in errors[field])


def register_payload(phone):
    return {
        'email': 'newcomer@example.com', 'full_name': 'New Comer', 'phone_number': phone,
        'password': 'Str0ng!Passw0rd#', 'password_confirm': 'Str0ng!Passw0rd#',
    }


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='guest@example.com', password='GuestPassword#123', phone_number='+998901112233',
    )


@pytest.mark.django_db
class TestRegister:

    def test_phone_number_sent_with_the_form_is_not_stored(self):
        response = APIClient().post(
            '/api/v1/auth/register/', register_payload('+998 90 123 45 67'), format='json'
        )
        assert response.status_code == 201, response.data
        assert User.objects.get(email='newcomer@example.com').phone_number is None

    def test_registration_needs_no_phone_number(self):
        payload = register_payload('')
        del payload['phone_number']
        response = APIClient().post('/api/v1/auth/register/', payload, format='json')
        assert response.status_code == 201, response.data


@pytest.mark.django_db
class TestBookingGuestPhone:

    @pytest.mark.parametrize('phone', INVALID_NUMBERS)
    def test_invalid_guest_phone_is_rejected(self, user, phone):
        client = APIClient()
        client.force_authenticate(user=user)
        check_in = date.today() + timedelta(days=3)
        response = client.post('/api/v1/bookings/', {
            'property_id': 1, 'room_type_id': 1, 'rate_plan_id': 1,
            'check_in': check_in.isoformat(), 'check_out': (check_in + timedelta(days=1)).isoformat(),
            'guest_count': 1, 'guest_phone': phone,
        }, format='json')
        assert response.status_code == 400
        # Booking errors use the standard envelope
        assert error_text(response, 'guest_phone', response.data['details']) == PHONE_ERROR
