"""
SECURITY_REVIEW M-5: registration answers the same for new and existing contacts.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Notification
from users.models import User

PASSWORD = 'Str0ng!Passw0rd#9'
URL = '/api/v1/auth/register/'


def payload(**overrides):
    data = {
        'email': 'newcomer@example.uz', 'full_name': 'New Comer', 'phone_number': '+998901230010',
        'password': PASSWORD, 'password_confirm': PASSWORD,
    }
    data.update(overrides)
    return data


class TestRegisterDoesNotRevealExistingContacts(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.existing = User.objects.create_user(
            email='taken@example.uz', password='Existing!Passw0rd#1', phone_number='+998901230011'
        )

    def _register(self, **overrides):
        return self.client.post(URL, payload(**overrides), format='json')

    def test_new_and_existing_email_get_the_same_response(self):
        new = self._register()
        existing = self._register(email='TAKEN@example.uz', phone_number='+998901230012')

        assert (new.status_code, new.json()) == (existing.status_code, existing.json())
        assert new.status_code == 202

    def test_existing_phone_gets_the_same_response_as_a_new_one(self):
        new = self._register()
        existing = self._register(email='another@example.uz', phone_number='+998901230011')

        assert (new.status_code, new.json()) == (existing.status_code, existing.json())

    def test_neither_response_starts_a_session(self):
        self._register()
        assert '_auth_user_id' not in self.client.session
        self._register(email='taken@example.uz', phone_number='+998901230013')
        assert '_auth_user_id' not in self.client.session

    def test_existing_account_is_untouched_and_no_duplicate_is_created(self):
        self._register(email='taken@example.uz', phone_number='+998901230014', full_name='Impostor')

        self.existing.refresh_from_db()
        assert self.existing.check_password('Existing!Passw0rd#1')
        assert self.existing.full_name != 'Impostor'
        assert User.objects.filter(email__iexact='taken@example.uz').count() == 1
        assert not User.objects.filter(phone_number='+998901230014').exists()

    def test_new_contact_creates_the_account(self):
        self._register()
        user = User.objects.get(email='newcomer@example.uz')
        assert user.check_password(PASSWORD)
        assert user.phone_number == '+998901230010'

    def test_existing_owner_is_notified_in_app(self):
        self._register(email='taken@example.uz', phone_number='+998901230015')
        notification = Notification.objects.get(user=self.existing)
        assert notification.code == 'registration_attempt'
        assert notification.notification_type == 'system'

    def test_existing_owner_is_notified_when_only_the_phone_matches(self):
        self._register(email='another@example.uz', phone_number='+998901230011')
        assert Notification.objects.filter(user=self.existing, code='registration_attempt').exists()

    def test_invalid_input_is_still_rejected(self):
        assert self._register(password='short', password_confirm='short').status_code == 400
        assert self._register(phone_number='12').status_code == 400
        assert self._register(password_confirm='Different!Passw0rd#2').status_code == 400
