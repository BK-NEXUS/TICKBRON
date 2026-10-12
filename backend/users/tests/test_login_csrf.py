"""
N-8 / L-3: login, register and the OTP endpoints need a CSRF token even for anonymous callers.

DRF only checks CSRF for a request that already has a session, so a cross-site form could
log a victim into the attacker's account (login CSRF): the victim's later bookings and
saved details would land in the attacker's account.
"""
import pytest
from rest_framework.test import APIClient

from users.models import User

PASSWORD = 'SecureP@ssw0rd123'
PHONE = '+998901112299'


@pytest.fixture
def browser():
    """A client that enforces CSRF like a real browser."""
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='csrf-login@example.com', password=PASSWORD, full_name='Csrf Login',
        phone_number=PHONE, phone_verified=True,
    )


def token_of(client):
    return client.get('/api/v1/auth/csrf/').data['csrf_token']


@pytest.mark.django_db
class TestLoginNeedsAToken:
    def test_login_without_a_token_is_refused(self, browser, user):
        response = browser.post('/api/v1/auth/login/', {'email': user.email, 'password': PASSWORD}, format='json')

        assert response.status_code == 403
        assert '_auth_user_id' not in browser.session

    def test_login_with_a_wrong_token_is_refused(self, browser, user):
        token_of(browser)

        response = browser.post(
            '/api/v1/auth/login/', {'email': user.email, 'password': PASSWORD}, format='json',
            HTTP_X_CSRFTOKEN='not-the-token',
        )

        assert response.status_code == 403

    def test_login_with_the_token_works(self, browser, user):
        token = token_of(browser)

        response = browser.post(
            '/api/v1/auth/login/', {'email': user.email, 'password': PASSWORD}, format='json', HTTP_X_CSRFTOKEN=token,
        )

        assert response.status_code == 200
        assert response.data['email'] == user.email

    def test_a_wrong_password_with_the_token_is_still_the_generic_401(self, browser, user):
        token = token_of(browser)

        response = browser.post(
            '/api/v1/auth/login/', {'email': user.email, 'password': 'wrong'}, format='json', HTTP_X_CSRFTOKEN=token,
        )

        assert response.status_code == 401


@pytest.mark.django_db
class TestOtherPublicPostsNeedAToken:
    def test_register_without_a_token_is_refused_and_creates_nothing(self, browser):
        response = browser.post('/api/v1/auth/register/', {
            'email': 'new@example.com', 'full_name': 'New User', 'phone_number': '+998901112288',
            'password': 'Str0ng#Pass-2026!', 'password_confirm': 'Str0ng#Pass-2026!',
        }, format='json')

        assert response.status_code == 403
        assert not User.objects.filter(email='new@example.com').exists()

    def test_otp_request_without_a_token_is_refused(self, browser, user):
        response = browser.post('/api/v1/auth/otp/request/', {'phone_number': PHONE}, format='json')

        assert response.status_code == 403
        user.refresh_from_db()
        assert user.otp_code is None

    def test_otp_verify_without_a_token_is_refused(self, browser, user):
        code = user.generate_otp()

        response = browser.post('/api/v1/auth/otp/verify/', {'phone_number': PHONE, 'otp_code': code}, format='json')

        assert response.status_code == 403
        assert '_auth_user_id' not in browser.session

    def test_otp_flow_with_the_token_works(self, browser, user):
        token = token_of(browser)
        requested = browser.post('/api/v1/auth/otp/request/', {'phone_number': PHONE}, format='json', HTTP_X_CSRFTOKEN=token)
        assert requested.status_code == 200

        verified = browser.post(
            '/api/v1/auth/otp/verify/', {'phone_number': PHONE, 'otp_code': requested.data['otp_code']},
            format='json', HTTP_X_CSRFTOKEN=token,
        )

        assert verified.status_code == 200
