"""Cash at the hotel (.ai/PLAN_CASH_ONLY.md stage 3): the online payment API and its settings are gone."""
import pytest
from django.conf import settings
from rest_framework.test import APIClient

from users.models import User

GONE = [
    ('post', '/api/v1/payments/transactions/'),
    ('get', '/api/v1/payments/transactions/'),
    ('post', '/api/v1/payments/webhook/payme/'),
    ('get', '/api/v1/payments/audit-logs/'),
    ('get', '/api/v1/admin-panel/payments/transactions/'),
    ('get', '/api/v1/admin-panel/refunds/needs-attention/'),
    ('post', '/api/v1/admin-panel/refunds/1/retry/'),
]


@pytest.fixture
def staff_client(db):
    client = APIClient()
    client.force_authenticate(User.objects.create_user(email='s@example.com', password='x', is_staff=True,
                                                       is_superuser=True))
    return client


@pytest.mark.django_db
@pytest.mark.parametrize('method, url', GONE)
def test_payment_endpoints_are_gone(staff_client, method, url):
    assert getattr(staff_client, method)(url, {}, format='json').status_code == 404


@pytest.mark.parametrize('name', [
    'PAYMENT_TEST_MODE', 'PAYME_SECRET_KEY', 'CLICK_SECRET_KEY', 'VISA_API_KEY',
    'NO_SHOW_REFUND_PERCENT', 'CANCEL_REFUND_PERCENT',
])
def test_payment_settings_are_gone(name):
    assert not hasattr(settings, name)


@pytest.mark.django_db
def test_the_customer_profile_has_no_payments(staff_client):
    customer = User.objects.create_user(email='c@example.com', password='x')
    data = staff_client.get(f'/api/v1/admin-panel/customers/{customer.id}/').data
    assert 'payments' not in data
