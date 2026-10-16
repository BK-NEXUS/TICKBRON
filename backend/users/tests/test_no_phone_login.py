"""
Accounts are e-mail only: there is no SMS login, no phone verification, and no endpoint that
takes a phone number for an account. An old number stays on the account, read-only.
"""
import pytest
from rest_framework.test import APIClient

from users.models import User

REMOVED_ENDPOINTS = [
    '/api/v1/auth/otp/request/',
    '/api/v1/auth/otp/verify/',
    '/api/v1/auth/phone/verify/request/',
    '/api/v1/auth/phone/verify/confirm/',
]
OLD_NUMBER = '+998901112233'


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='guest@example.com', password='GuestPassword#123', phone_number=OLD_NUMBER,
    )


@pytest.mark.django_db
class TestRemovedEndpoints:

    @pytest.mark.parametrize('url', REMOVED_ENDPOINTS)
    def test_anonymous_gets_404(self, url):
        response = APIClient().post(url, {'phone_number': OLD_NUMBER, 'otp_code': '123456'}, format='json')

        assert response.status_code == 404

    @pytest.mark.parametrize('url', REMOVED_ENDPOINTS)
    def test_signed_in_user_gets_404(self, user, url):
        client = APIClient()
        client.force_authenticate(user=user)

        assert client.post(url, {'otp_code': '123456'}, format='json').status_code == 404

    def test_a_phone_and_code_cannot_log_anyone_in(self, user):
        client = APIClient()
        client.post('/api/v1/auth/otp/verify/', {'phone_number': OLD_NUMBER, 'otp_code': '123456'}, format='json')

        assert client.get('/api/v1/auth/me/').status_code == 401


@pytest.mark.django_db
class TestPhoneIsNotAccepted:

    def test_profile_update_ignores_a_phone_number(self, user):
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.patch('/api/v1/auth/me/update/', {'phone_number': '+998915554433', 'telegram': '@guest'},
                                format='json')

        assert response.status_code == 200, response.data
        user.refresh_from_db()
        assert user.phone_number == OLD_NUMBER
        assert user.telegram == '@guest'

    def test_old_number_is_still_returned_read_only(self, user):
        client = APIClient()
        client.force_authenticate(user=user)

        assert client.get('/api/v1/auth/me/').data['phone_number'] == OLD_NUMBER

    def test_create_hotel_owner_ignores_a_phone_number(self, db):
        admin = User.objects.create_superuser(email='admin@example.com', password='AdminPassword#123')
        client = APIClient()
        client.force_authenticate(user=admin)

        response = client.post('/api/v1/admin-panel/users/create-hotel-owner/', {
            'email': 'owner@example.com', 'first_name': 'Hotel', 'last_name': 'Owner',
            'phone_number': OLD_NUMBER, 'password': 'Owner#Secret2026', 'password_confirm': 'Owner#Secret2026',
        }, format='json')

        assert response.status_code == 201, response.data
        assert not User.objects.get(email='owner@example.com').phone_number
