"""
Server-side phone number validation: every endpoint that takes a phone number
accepts only a valid international number and stores it as E.164.
"""
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient, APIRequestFactory

from users.models import User
from users.views import OTPRequestRateThrottle

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
        email='guest@example.com', password='GuestPassword#123', phone_number='+998901112233'
    )


@pytest.mark.django_db
class TestRegister:

    @pytest.mark.parametrize('phone', INVALID_NUMBERS)
    def test_invalid_number_is_rejected_with_a_clear_message(self, phone):
        response = APIClient().post('/api/v1/auth/register/', register_payload(phone), format='json')
        assert response.status_code == 400
        assert error_text(response) == PHONE_ERROR
        assert not User.objects.filter(email='newcomer@example.com').exists()

    def test_formatted_number_is_stored_as_e164(self):
        response = APIClient().post(
            '/api/v1/auth/register/', register_payload('+998 90 123 45 67'), format='json'
        )
        assert response.status_code == 201, response.data
        assert User.objects.get(email='newcomer@example.com').phone_number == '+998901234567'

    def test_formatted_duplicate_is_caught(self, user):
        response = APIClient().post(
            '/api/v1/auth/register/', register_payload('+998 90 111 22 33'), format='json'
        )
        assert response.status_code == 400
        assert 'already exists' in error_text(response)


@pytest.mark.django_db
class TestProfileUpdate:

    @pytest.mark.parametrize('phone', INVALID_NUMBERS)
    def test_invalid_number_is_rejected(self, user, phone):
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch('/api/v1/auth/me/update/', {'phone_number': phone}, format='json')
        assert response.status_code == 400
        assert error_text(response) == PHONE_ERROR
        user.refresh_from_db()
        assert user.phone_number == '+998901112233'

    def test_formatted_number_is_normalized(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch('/api/v1/auth/me/update/', {'phone_number': '+998 33 123 45 67'},
                                format='json')
        assert response.status_code == 200
        assert response.data['phone_number'] == '+998331234567'

    def test_blank_still_clears_the_number(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch('/api/v1/auth/me/update/', {'phone_number': ''}, format='json')
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.phone_number is None


@pytest.mark.django_db
class TestOTP:

    @pytest.mark.parametrize('phone', INVALID_NUMBERS)
    def test_request_rejects_invalid_number(self, phone):
        response = APIClient().post('/api/v1/auth/otp/request/', {'phone_number': phone}, format='json')
        assert response.status_code == 400
        assert error_text(response) == PHONE_ERROR

    @pytest.mark.parametrize('phone', INVALID_NUMBERS)
    def test_verify_rejects_invalid_number(self, phone):
        response = APIClient().post('/api/v1/auth/otp/verify/', {
            'phone_number': phone, 'otp_code': '123456',
        }, format='json')
        assert response.status_code == 400
        assert error_text(response) == PHONE_ERROR

    def test_formatted_number_logs_in(self, user):
        client = APIClient()
        request = client.post('/api/v1/auth/otp/request/', {'phone_number': '+998 90 111 22 33'},
                              format='json')
        assert request.status_code == 200
        verify = client.post('/api/v1/auth/otp/verify/', {
            'phone_number': '+998 90 111 22 33', 'otp_code': request.data['otp_code'],
        }, format='json')
        assert verify.status_code == 200
        assert verify.data['id'] == user.id

    def test_throttle_uses_one_bucket_for_every_spelling_of_a_number(self):
        factory = APIRequestFactory()
        throttle = OTPRequestRateThrottle()

        def key(phone):
            request = factory.post('/api/v1/auth/otp/request/', {'phone_number': phone}, format='json')
            request.data = {'phone_number': phone}
            return throttle.get_cache_key(request, None)

        assert key('+998 90 111 22 33') == key('+998901112233') == key(' +998-90-111-22-33 ')


@pytest.mark.django_db
class TestAdminCreateHotelOwner:

    def payload(self, phone):
        return {
            'email': 'owner@example.com', 'first_name': 'Hotel', 'last_name': 'Owner',
            'phone_number': phone, 'password': 'OwnerPassword#123', 'password_confirm': 'OwnerPassword#123',
        }

    @pytest.fixture
    def admin_client(self, db):
        admin = User.objects.create_superuser(email='admin@example.com', password='AdminPassword#123')
        client = APIClient()
        client.force_authenticate(user=admin)
        return client

    @pytest.mark.parametrize('phone', INVALID_NUMBERS)
    def test_invalid_number_is_rejected(self, admin_client, phone):
        response = admin_client.post('/api/v1/admin-panel/users/create-hotel-owner/',
                                     self.payload(phone), format='json')
        assert response.status_code == 400
        assert error_text(response) == PHONE_ERROR

    def test_number_is_optional_and_normalized(self, admin_client):
        blank = admin_client.post('/api/v1/admin-panel/users/create-hotel-owner/',
                                  self.payload(''), format='json')
        assert blank.status_code == 201, blank.data

        payload = {**self.payload('+998 91 555 44 33'), 'email': 'owner2@example.com'}
        formatted = admin_client.post('/api/v1/admin-panel/users/create-hotel-owner/', payload,
                                      format='json')
        assert formatted.status_code == 201, formatted.data
        assert User.objects.get(email='owner2@example.com').phone_number == '+998915554433'


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
