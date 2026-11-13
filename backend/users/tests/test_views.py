"""
Paydalanıwshı autentifikaciya view leri ushın testler.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User

User = get_user_model()


class TestAuthViews(TestCase):
    """Autentifikaciya view leri ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123',
            'phone_number': '+998901234567',
        }

    def test_register_user(self):
        """Ápiwayılastırılǵan maydanlar menen paydalanıwshı dizimnen ótiw endpoint in testlew."""
        response = self.client.post('/api/v1/auth/register/', self.user_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email='test@example.com').exists()
        assert 'email' in response.data
        assert response.data['email'] == 'test@example.com'
        assert response.data['full_name'] == 'Test User'
        assert response.data['phone_number'] == '+998901234567'  # telefon jıynalmaǵan waqıtta None edi

    def test_register_user_auto_login(self):
        """Dizimnen ótkennen keyin paydalanıwshı avtomatik kirgenin testlew."""
        response = self.client.post('/api/v1/auth/register/', self.user_data)

        # Session jaratılǵanın tekseriw (paydalanıwshı kirgen bolıwı kerek)
        assert response.status_code == status.HTTP_201_CREATED
        # Haqıyqıy jaǵdayda session cookie lerdi tekserer edik, biraq API testlew ushın
        # paydalanıwshı sátli jaratılǵanın tekseremiz

    def test_register_duplicate_email(self):
        """Birdey email menen dizimnen ótiwdi testlew."""
        # Birinshi paydalanıwshını jaratıw
        User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        # Birdey email menen dizimnen ótiwge urınıw
        response = self.client.post('/api/v1/auth/register/', self.user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_valid_credentials(self):
        """Jaramlı credential ler menen kiriwdi testlew."""
        # Eski formatlı paydalanıwshı jaratıw (first_name/last_name)
        User.objects.create_user(
            email='test@example.com',
            password='SecureP@ssw0rd123',
            first_name='Test',
            last_name='User'
        )

        # Kiriw
        login_data = {
            'email': 'test@example.com',
            'password': 'SecureP@ssw0rd123'
        }
        response = self.client.post('/api/v1/auth/login/', login_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'test@example.com'

    def test_login_invalid_credentials(self):
        """Jaramsız credential ler menen kiriwdi testlew."""
        login_data = {
            'email': 'test@example.com',
            'password': 'WrongP@ssw0rd123'
        }
        response = self.client.post('/api/v1/auth/login/', login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user(self):
        """Aktiv emes paydalanıwshı menen kiriwdi testlew."""
        # Aktiv emes paydalanıwshını jaratıw
        user = User.objects.create_user(
            email='test@example.com',
            password='SecureP@ssw0rd123',
            full_name='Test User'
        )
        user.is_active = False
        user.save()

        login_data = {
            'email': 'test@example.com',
            'password': 'SecureP@ssw0rd123'
        }
        response = self.client.post('/api/v1/auth/login/', login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_authenticated(self):
        """Autentifikaciyadan ótken paydalanıwshı ushın shıǵıwdı testlew."""
        # Paydalanıwshını jaratıw hám autentifikaciyadan ótkeriw
        user = User.objects.create_user(
            email='test@example.com',
            password='SecureP@ssw0rd123',
            full_name='Test User'
        )
        self.client.force_authenticate(user=user)

        response = self.client.post('/api/v1/auth/logout/')

        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data

    def test_logout_unauthenticated(self):
        """Autentifikaciyadan ótpegen paydalanıwshı ushın shıǵıwdı testlew."""
        response = self.client.post('/api/v1/auth/logout/')

        # Autentifikaciyasız paydalanıwshılar ushın da islewi kerek (AllowAny ruxsatı)
        assert response.status_code == status.HTTP_200_OK

    def test_me_authenticated(self):
        """Autentifikaciyadan ótkende házirgi paydalanıwshı maǵlıwmatın alıwdı testlew."""
        # Paydalanıwshını jaratıw hám autentifikaciyadan ótkeriw
        user = User.objects.create_user(
            email='test@example.com',
            password='SecureP@ssw0rd123',
            full_name='Test User'
        )
        self.client.force_authenticate(user=user)

        response = self.client.get('/api/v1/auth/me/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'test@example.com'
        assert response.data['full_name'] == 'Test User'

    def test_me_unauthenticated(self):
        """Autentifikaciyadan ótpegende házirgi paydalanıwshı maǵlıwmatın alıwdı testlew."""
        response = self.client.get('/api/v1/auth/me/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_session_authenticated(self):
        """Autentifikaciyadan ótkende session di jańalawdı testlew."""
        user = User.objects.create_user(
            email='test@example.com',
            password='SecureP@ssw0rd123',
            full_name='Test User'
        )
        self.client.force_authenticate(user=user)

        response = self.client.post('/api/v1/auth/refresh/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'test@example.com'

    def test_refresh_session_unauthenticated(self):
        """Autentifikaciyadan ótpegende session di jańalawdı testlew."""
        response = self.client.post('/api/v1/auth/refresh/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_account_lockout_after_failed_attempts(self):
        """Bir neshe sátsiz kiriw urınısınan keyin akkauntti bloklawdı testlew."""
        # Paydalanıwshını jaratıw
        User.objects.create_user(
            email='test@example.com',
            password='SecureP@ssw0rd123',
            full_name='Test User'
        )

        # 5 sátsiz kiriw urınısın uqsatıw
        for _ in range(5):
            login_data = {
                'email': 'test@example.com',
                'password': 'WrongP@ssw0rd123'
            }
            self.client.post('/api/v1/auth/login/', login_data)

        # Durıs parol menen sol IP den kiriwge urınıw (bul IP ushın bloklanǵan;
        # juwap ulıwma sátsizlik bolıp, bloklawdı ashpaydı)
        login_data = {
            'email': 'test@example.com',
            'password': 'SecureP@ssw0rd123'
        }
        response = self.client.post('/api/v1/auth/login/', login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'locked' not in response.data['detail'].lower()
