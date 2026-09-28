"""
GET /auth/csrf/ also says whether the session is logged in, so the SPA only asks
/auth/me/ when there is a session (no 401 console error for every anonymous page view).
"""
from django.test import TestCase
from rest_framework.test import APIClient

from users.models import User

CSRF_URL = '/api/v1/auth/csrf/'


class TestCsrfSessionFlag(TestCase):
    def test_anonymous_is_not_authenticated(self):
        response = APIClient().get(CSRF_URL)
        assert response.status_code == 200
        assert response.data['authenticated'] is False
        assert response.data['csrf_token']

    def test_logged_in_is_authenticated(self):
        client = APIClient()
        client.force_login(User.objects.create_user(email='someone@example.com', password='x'))
        response = client.get(CSRF_URL)
        assert response.status_code == 200
        assert response.data['authenticated'] is True
        assert response.data['csrf_token']
