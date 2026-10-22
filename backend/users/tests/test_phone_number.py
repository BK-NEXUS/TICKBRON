"""
The phone number is back (plan .ai/PLAN_CASH_ONLY.md stage 1): required at sign-up, in the profile,
for an admin-created hotel-owner account and in a booking. It is only stored: no SMS, no code, no
verification, no uniqueness rule.
"""
import pytest
from rest_framework.test import APIClient

from partner.tests.geography_helpers import uzbek_location
from users.models import User

REGISTER = '/api/v1/auth/register/'
PROFILE = '/api/v1/auth/me/update/'
CREATE_OWNER = '/api/v1/admin-panel/users/create-hotel-owner/'
PASSWORD = 'Str0ng#Passw0rd-2026'


def signup(client, **extra):
    body = {'email': 'new@example.com', 'full_name': 'Ali Valiyev', 'password': PASSWORD, 'password_confirm': PASSWORD,
            'phone_number': '+998 90 123-45-67'}
    body.update(extra)
    return client.post(REGISTER, body, format='json')


@pytest.mark.django_db
class TestRegister:
    def test_the_number_is_stored_in_e164_form(self):
        response = signup(APIClient())
        assert response.status_code == 201, response.data
        assert User.objects.get(email='new@example.com').phone_number == '+998901234567'
        assert response.data['phone_number'] == '+998901234567'

    def test_it_is_required(self):
        body = {'email': 'new@example.com', 'full_name': 'Ali Valiyev', 'password': PASSWORD, 'password_confirm': PASSWORD}
        response = APIClient().post(REGISTER, body, format='json')
        assert response.status_code == 400
        assert not User.objects.filter(email='new@example.com').exists()

    @pytest.mark.parametrize('number', ['', '12345', 'abc', '+99890', '+998 90 123 45 6a', '90 123 45 67'])
    def test_a_bad_number_is_refused_and_creates_nothing(self, number):
        response = signup(APIClient(), phone_number=number)
        assert response.status_code == 400
        assert not User.objects.filter(email='new@example.com').exists()

    def test_two_accounts_may_share_a_number(self):
        assert signup(APIClient()).status_code == 201
        assert signup(APIClient(), email='other@example.com').status_code == 201

    def test_nothing_is_sent_and_no_code_endpoint_exists(self):
        signup(APIClient())
        assert APIClient().post('/api/v1/auth/otp/request/', {'phone_number': '+998901234567'}, format='json').status_code == 404


@pytest.mark.django_db
class TestProfile:
    @pytest.fixture
    def client(self):
        user = User.objects.create_user(email='p@example.com', password=PASSWORD, phone_number='+998901112233')
        api = APIClient()
        api.force_authenticate(user)
        api.user = user
        return api

    def test_the_number_can_be_changed(self, client):
        response = client.patch(PROFILE, {'phone_number': '+998 91 555 44 33'}, format='json')
        assert response.status_code == 200, response.data
        client.user.refresh_from_db()
        assert client.user.phone_number == '+998915554433'

    @pytest.mark.parametrize('number', ['', '123', 'phone'])
    def test_a_bad_or_blank_number_is_refused_and_the_old_one_stays(self, client, number):
        assert client.patch(PROFILE, {'phone_number': number}, format='json').status_code == 400
        client.user.refresh_from_db()
        assert client.user.phone_number == '+998901112233'

    def test_other_fields_can_be_changed_without_sending_the_number(self, client):
        assert client.patch(PROFILE, {'telegram': '@guest'}, format='json').status_code == 200

    def test_an_old_account_without_a_number_can_still_edit_other_fields(self):
        user = User.objects.create_user(email='old@example.com', password=PASSWORD)
        api = APIClient()
        api.force_authenticate(user)
        assert api.patch(PROFILE, {'telegram': '@old'}, format='json').status_code == 200


@pytest.mark.django_db
class TestAdminCreatesAnOwner:
    @pytest.fixture
    def client(self):
        admin = User.objects.create_superuser(email='admin@example.com', password='AdminPassword#123')
        api = APIClient()
        api.force_authenticate(admin)
        return api

    def body(self, **extra):
        body = {'email': 'owner@example.com', 'first_name': 'Hotel', 'last_name': 'Owner',
                'password': 'Owner#Secret2026', 'password_confirm': 'Owner#Secret2026',
                'phone_number': '+998 90 111 22 33', **uzbek_location('Tashkent')}
        body.update(extra)
        return body

    def test_the_number_is_stored(self, client):
        response = client.post(CREATE_OWNER, self.body(), format='json')
        assert response.status_code == 201, response.data
        assert User.objects.get(email='owner@example.com').phone_number == '+998901112233'

    def test_it_is_required_and_creates_nothing_without_it(self, client):
        body = self.body()
        del body['phone_number']
        assert client.post(CREATE_OWNER, body, format='json').status_code == 400
        assert not User.objects.filter(email='owner@example.com').exists()

    def test_a_bad_number_is_refused(self, client):
        assert client.post(CREATE_OWNER, self.body(phone_number='nope'), format='json').status_code == 400
        assert not User.objects.filter(email='owner@example.com').exists()
