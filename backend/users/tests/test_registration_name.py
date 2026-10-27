"""QA finding F9: sign-up with an empty name created the account with the e-mail address as the name."""
import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from users.models import User

PASSWORD = 'Str0ng#Passw0rd-2026'


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


def signup(**extra):
    body = {'email': 'new@example.com', 'full_name': 'Ali Valiyev', 'password': PASSWORD,
            'password_confirm': PASSWORD, 'phone_number': '+998901234567', **extra}
    return APIClient().post('/api/v1/auth/register/', body, format='json')


@pytest.mark.django_db
class TestRegistrationNeedsAName:
    @pytest.mark.parametrize('name', ['', '   ', '\t'])
    def test_blank_name_is_refused(self, name):
        response = signup(full_name=name)
        assert response.status_code == 400
        assert 'full_name' in response.data
        assert not User.objects.filter(email='new@example.com').exists()

    def test_a_missing_name_is_refused(self):
        body = {'email': 'new@example.com', 'password': PASSWORD, 'password_confirm': PASSWORD,
                'phone_number': '+998901234567'}
        response = APIClient().post('/api/v1/auth/register/', body, format='json')
        assert response.status_code == 400
        assert 'full_name' in response.data

    def test_a_real_name_is_kept(self):
        response = signup(full_name='  Ali Valiyev ')
        assert response.status_code == 201, response.data
        assert User.objects.get(email='new@example.com').full_name == 'Ali Valiyev'
