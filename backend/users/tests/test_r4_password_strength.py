"""
R4 qáwipsizlik tekseriwi: parol qaǵıydaları parol qoyatuǵın hár bir API da májbúrlenedi.

Burın dizimnen ótiw hám super-admin "mehmanxana iyesin jaratıw" endpoint i tek
min_length=12 di tekseretuǵın edi, sol sebepli 'aaaaaaaaaaaa' yamasa 'password1234' qabıllanatuǵın edi.
AUTH_PASSWORD_VALIDATORS (users.validators.StrongPasswordValidator di qosqanda)
endi ekewinde de isleydi.
"""
import pytest
from rest_framework.test import APIClient

from partner.tests.geography_helpers import uzbek_location
from users.models import User

REGISTER_URL = '/api/v1/auth/register/'
CREATE_OWNER_URL = '/api/v1/admin-panel/users/create-hotel-owner/'

WEAK_PASSWORDS = [
    'aaaaaaaaaaaa',        # bir belgi qaytalanǵan
    'password1234',        # keń tarqalǵan
    'tickbronhotel',       # tek kishi háripler
    '847261930475',        # tek sanlar
    'Tashkent2026stay',    # arnawlı belgi joq
]
STRONG_PASSWORD = 'Tashkent#Stay2026'


def _register(client, password, n):
    return client.post(REGISTER_URL, {
        'email': f'guest{n}@example.com', 'full_name': 'Guest Person',
        'phone_number': f'+99890111{n:04d}', 'password': password, 'password_confirm': password,
    }, format='json')


@pytest.mark.django_db
@pytest.mark.parametrize('password', WEAK_PASSWORDS)
def test_register_rejects_weak_password(password):
    response = _register(APIClient(), password, WEAK_PASSWORDS.index(password))

    assert response.status_code == 400
    assert 'password' in str(response.data)
    assert not User.objects.filter(email__startswith='guest').exists()


@pytest.mark.django_db
def test_register_accepts_strong_password():
    response = _register(APIClient(), STRONG_PASSWORD, 99)

    assert response.status_code == 201


@pytest.mark.django_db
def test_register_rejects_password_similar_to_email():
    client = APIClient()
    response = client.post(REGISTER_URL, {
        'email': 'samarkand.traveller@example.com', 'full_name': 'Guest Person',
        'phone_number': '+998901119999', 'password': 'Samarkand.Traveller1',
        'password_confirm': 'Samarkand.Traveller1',
    }, format='json')

    assert response.status_code == 400


@pytest.fixture
def superadmin_client():
    admin = User.objects.create_user(
        email='root@example.com', password='x', is_staff=True, is_superuser=True,
    )
    client = APIClient()
    client.force_authenticate(user=admin)
    return client


def _create_owner(client, password, n):
    return client.post(CREATE_OWNER_URL, {
        'email': f'owner{n}@example.com', 'first_name': 'Hotel', 'last_name': 'Owner',
        'password': password, 'password_confirm': password,
        **uzbek_location('Tashkent'),  # jańa akkauntqa orın kerek
        'phone_number': '+998901112233',  # jańa akkauntqa telefon nomeri kerek
    }, format='json')


@pytest.mark.django_db
@pytest.mark.parametrize('password', WEAK_PASSWORDS)
def test_create_hotel_owner_rejects_weak_password(superadmin_client, password):
    response = _create_owner(superadmin_client, password, WEAK_PASSWORDS.index(password))

    assert response.status_code == 400
    assert 'password' in str(response.data)
    assert not User.objects.filter(email__startswith='owner').exists()


@pytest.mark.django_db
def test_create_hotel_owner_accepts_strong_password(superadmin_client):
    response = _create_owner(superadmin_client, STRONG_PASSWORD, 99)

    assert response.status_code == 201
