"""L-2: the API schema and docs are an inventory of every endpoint; hide them in production."""
import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from users.models import User

DOC_URLS = ['/api/schema/', '/api/docs/', '/api/redoc/']


@pytest.fixture
def staff_client(db):
    user = User.objects.create_user(email='docs-staff@example.com', password='x-pass-123', is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def guest_client(db):
    user = User.objects.create_user(email='docs-guest@example.com', password='x-pass-123')
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
@pytest.mark.parametrize('url', DOC_URLS)
@override_settings(DEBUG=False)
def test_docs_are_hidden_from_anonymous_and_guests_in_production(url, guest_client):
    assert APIClient().get(url).status_code in (401, 403)
    assert guest_client.get(url).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize('url', DOC_URLS)
@override_settings(DEBUG=False)
def test_docs_are_open_to_staff_in_production(url, staff_client):
    assert staff_client.get(url).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize('url', DOC_URLS)
@override_settings(DEBUG=True)
def test_docs_are_open_in_development(url):
    assert APIClient().get(url).status_code == 200
