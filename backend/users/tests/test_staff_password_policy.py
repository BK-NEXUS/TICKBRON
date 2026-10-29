"""
Administrators and staff follow the same password rule as everybody else: at least 8 characters with a letter,
a digit and a special character (the owner dropped the longer staff rule: people forget such passwords).
It holds where a staff password is set: adding an administrator, changing it, and the reset link.
"""
import pytest
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from users.models import User

OLD = 'old-Pass#1234'
SEVEN = 'kit7$ab'
EIGHT = 'kitob7$y'
CREATE = '/api/v1/admin-panel/users/create-admin/'
CHANGE = '/api/v1/auth/password/change/'
RESET = '/api/v1/auth/password-reset/confirm/'


def body(password, **extra):
    return {'email': 'new.admin@example.com', 'first_name': 'Aziza', 'last_name': 'Karimova',
            'phone_number': '+998901234567', 'password': password, 'password_confirm': password, **extra}


def signed_in(**flags):
    user = User.objects.create_user(email=f'u{User.objects.count()}@example.com', password=OLD, **flags)
    api = APIClient()
    api.force_authenticate(user=user)
    return api, user


def test_the_two_lengths_are_what_the_rule_says():
    assert (len(SEVEN), len(EIGHT)) == (7, 8)


@pytest.mark.django_db
class TestAddingAnAdministrator:
    def test_seven_characters_are_refused(self):
        api, _ = signed_in(is_staff=True, is_superuser=True)
        response = api.post(CREATE, body(SEVEN), format='json')
        assert response.status_code == 400
        assert 'password' in response.data
        assert not User.objects.filter(email='new.admin@example.com').exists()

    def test_eight_characters_are_accepted(self):
        api, _ = signed_in(is_staff=True, is_superuser=True)
        assert api.post(CREATE, body(EIGHT), format='json').status_code == 201


@pytest.mark.django_db
class TestChangingAStaffPassword:
    def change(self, api, password):
        return api.post(CHANGE, {'current_password': OLD, 'password': password, 'password_confirm': password},
                        format='json')

    @pytest.mark.parametrize('flags', [{'is_staff': True}, {'is_staff': True, 'is_superuser': True}])
    def test_staff_and_super_admin_need_eight(self, flags):
        api, _ = signed_in(**flags)
        refused = self.change(api, SEVEN)
        assert refused.status_code == 400 and 'password' in refused.data
        assert self.change(api, EIGHT).status_code == 200

    def test_a_guest_needs_the_same_eight(self):
        api, _ = signed_in()
        assert self.change(api, SEVEN).status_code == 400
        assert self.change(api, EIGHT).status_code == 200


@pytest.mark.django_db
class TestResettingAStaffPassword:
    def reset(self, user, password):
        return APIClient().post(RESET, {
            'uid': urlsafe_base64_encode(force_bytes(user.pk)), 'token': default_token_generator.make_token(user),
            'password': password, 'password_confirm': password}, format='json')

    def test_staff_need_eight(self):
        user = User.objects.create_user(email='s@example.com', password=OLD, is_staff=True)
        refused = self.reset(user, SEVEN)
        assert refused.status_code == 400 and 'password' in refused.data
        assert self.reset(user, EIGHT).status_code == 200

    def test_a_guest_needs_the_same_eight(self):
        user = User.objects.create_user(email='g@example.com', password=OLD)
        assert self.reset(user, SEVEN).status_code == 400
        assert self.reset(user, EIGHT).status_code == 200
