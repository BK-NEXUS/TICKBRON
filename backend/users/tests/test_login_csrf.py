"""
N-8 / L-3: kiriw, dizimnen ótiw hám OTP endpoint lerine anonim sorawlarda da CSRF token kerek.

DRF CSRF di tek session i bar sorawlar ushın tekseredi, sol sebepli basqa saytdan forma
jábirleniwshini hújimshiniń akkauntına kirgize aladı (login CSRF): jábirleniwshiniń keyingi
bronları hám saqlanǵan maǵlıwmatları hújimshiniń akkauntına túsedi.
"""
import pytest
from rest_framework.test import APIClient

from users.models import User

PASSWORD = 'SecureP@ssw0rd123'
PHONE = '+998901112299'


@pytest.fixture
def browser():
    """CSRF di haqıyqıy brauzerdey májbúrleytuǵın client."""
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='csrf-login@example.com', password=PASSWORD, full_name='Csrf Login',
        phone_number=PHONE,
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
