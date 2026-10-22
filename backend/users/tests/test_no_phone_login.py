"""
There is no SMS login and no phone verification: the removed endpoints answer 404 and a phone and a
code cannot log anyone in. The number itself is only stored data (see test_phone_number.py).
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
class TestOldNumberStaysVisible:

    def test_old_number_is_still_returned_read_only(self, user):
        client = APIClient()
        client.force_authenticate(user=user)

        assert client.get('/api/v1/auth/me/').data['phone_number'] == OLD_NUMBER
