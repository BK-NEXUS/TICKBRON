"""
Tests for GET /api/v1/auth/csrf/ and the is_staff flag on /auth/me/.

The client enforces CSRF like a browser would, so these cover the full SPA
flow: fetch token -> send it in X-CSRFToken -> refetch after login.
"""
import pytest
from django.conf import settings
from rest_framework.test import APIClient

from users.models import User

PASSWORD = 'SecureP@ssw0rd123'


@pytest.fixture
def client():
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='csrf@example.com', password=PASSWORD, full_name='Csrf User',
        phone_number='+998901112233',
    )


def _token(client):
    response = client.get('/api/v1/auth/csrf/')
    assert response.status_code == 200
    return response.data['csrf_token']


def _login(client, user):
    response = client.post('/api/v1/auth/login/', {'email': user.email, 'password': PASSWORD}, format='json')
    assert response.status_code == 200
    return response


@pytest.mark.django_db
class TestCsrfEndpoint:
    def test_anonymous_gets_token_and_httponly_cookie(self, client):
        response = client.get('/api/v1/auth/csrf/')

        assert response.status_code == 200
        assert response.data['csrf_token']
        cookie = response.cookies[settings.CSRF_COOKIE_NAME]
        assert cookie['httponly']

    def test_authenticated_post_without_token_is_rejected(self, client, user):
        _login(client, user)

        response = client.post('/api/v1/auth/logout/')

        assert response.status_code == 403

    def test_authenticated_post_with_token_succeeds(self, client, user):
        _login(client, user)
        token = _token(client)

        response = client.post('/api/v1/auth/logout/', HTTP_X_CSRFTOKEN=token)

        assert response.status_code == 200

    def test_token_from_before_login_is_rotated(self, client, user):
        old_token = _token(client)
        _login(client, user)

        stale = client.post('/api/v1/auth/refresh/', HTTP_X_CSRFTOKEN=old_token)
        fresh = client.post('/api/v1/auth/refresh/', HTTP_X_CSRFTOKEN=_token(client))

        assert stale.status_code == 403
        assert fresh.status_code == 200


@pytest.mark.django_db
class TestMeIsStaff:
    def test_regular_user_is_not_staff(self, user):
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/v1/auth/me/')

        assert response.status_code == 200
        assert response.data['is_staff'] is False

    def test_staff_user_is_staff(self, user):
        user.is_staff = True
        user.save(update_fields=['is_staff'])
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/v1/auth/me/')

        assert response.data['is_staff'] is True

    def test_is_staff_cannot_be_set_through_profile_update(self, user):
        client = APIClient()
        client.force_authenticate(user=user)

        client.patch('/api/v1/auth/me/update/', {'is_staff': True}, format='json')

        user.refresh_from_db()
        assert user.is_staff is False
