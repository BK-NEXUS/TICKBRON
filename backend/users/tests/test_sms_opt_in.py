"""The user's consent to SMS about answers of the support team (plan .ai/PLAN_SMS_CHAT.md): off until the user turns it on."""
import pytest
from rest_framework.test import APIClient

from users.models import User

pytestmark = pytest.mark.django_db
PROFILE = '/api/v1/auth/me/update/'
PASSWORD = 'Str0ng#Passw0rd-2026'


@pytest.fixture
def user():
    return User.objects.create_user(email='sms-optin@example.com', password=PASSWORD, full_name='Sms Optin')


@pytest.fixture
def client(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


def test_a_new_account_has_not_agreed_to_sms(user):
    assert user.sms_notifications is False


def test_the_profile_answer_shows_the_choice(client):
    response = client.patch(PROFILE, {'full_name': 'Sms Optin'}, format='json')
    assert response.status_code == 200
    assert response.data['sms_notifications'] is False


def test_the_user_can_turn_it_on_and_off(client, user):
    on = client.patch(PROFILE, {'sms_notifications': True}, format='json')
    assert on.status_code == 200 and on.data['sms_notifications'] is True
    user.refresh_from_db()
    assert user.sms_notifications is True

    off = client.patch(PROFILE, {'sms_notifications': False}, format='json')
    assert off.status_code == 200 and off.data['sms_notifications'] is False
    user.refresh_from_db()
    assert user.sms_notifications is False


def test_a_value_that_is_not_true_or_false_is_refused(client, user):
    response = client.patch(PROFILE, {'sms_notifications': 'maybe'}, format='json')
    assert response.status_code == 400
    user.refresh_from_db()
    assert user.sms_notifications is False


def test_a_signed_out_visitor_cannot_change_it():
    response = APIClient().patch(PROFILE, {'sms_notifications': True}, format='json')
    assert response.status_code in (401, 403)
