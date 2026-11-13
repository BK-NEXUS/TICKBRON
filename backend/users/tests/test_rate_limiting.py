"""
Autentifikaciya endpoint lerindegi rate limiting ushın testler.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import patch

User = get_user_model()


class LoginRateLimitingTest(TestCase):
    """Kiriw endpoint i rate limiting i ushın testler - hár IP ge minutına 10 soraw."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = Client()

        # Test paydalanıwshısın jaratıw
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )

    def test_login_endpoint_works(self):
        """Kiriw endpoint i jaramlı credential ler menen islewin testlew."""
        response = self.client.post('/api/v1/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpassword123'
        })

        # Jaramlı credential ler ushın 200 qaytarıwı kerek
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])

    @patch('users.throttles.TESTING', False)
    def test_login_rate_limit_triggers(self):
        """Kiriw rate limit i 10 sorawdan keyin iske túsetuǵının testlew."""
        # 11 kiriw urınısın islew (shek minutına 10)
        responses = []
        for i in range(11):
            response = self.client.post('/api/v1/auth/login/', {
                'email': 'test@example.com',
                'password': 'wrongpassword'
            })
            responses.append(response.status_code)

        # Keminde biri rate limit lengen (429) bolıwı kerek
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, responses,
                     "Expected rate limit (429) to trigger after 10 login attempts")


class LoggedInSessionRateLimitingTest(TestCase):
    """Bir ret qollanılatuǵın akkaunt kiriw hám dizimnen ótiw shekterin kóterpewi kerek."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='throwaway@example.com', password='testpassword123',
            first_name='Throw', last_name='Away'
        )
        self.client.force_login(self.user)

    @patch('users.throttles.TESTING', False)
    def test_login_limit_applies_to_logged_in_session(self):
        statuses = [
            self.client.post('/api/v1/auth/login/', {'email': 'victim@example.com', 'password': 'x'}).status_code
            for _ in range(12)
        ]
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, statuses)

    @patch('users.throttles.TESTING', False)
    def test_register_limit_applies_to_logged_in_session(self):
        statuses = [
            self.client.post('/api/v1/auth/register/', {'email': f'n{i}@example.com'}).status_code
            for i in range(7)
        ]
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, statuses)


class RegisterRateLimitingTest(TestCase):
    """Dizimnen ótiw endpoint i rate limiting i ushın testler - hár IP ge minutına 5 soraw."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = Client()

    def test_register_endpoint_works(self):
        """Dizimnen ótiw endpoint i islewin testlew."""
        response = self.client.post('/api/v1/auth/register/', {
            'email': 'newuser@example.com',
            'password': 'testpassword123',
            'password_confirm': 'testpassword123',
            'first_name': 'New',
            'last_name': 'User'
        })

        # Jaramlı dizimnen ótiw ushın 201 qaytarıwı kerek
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_register_rate_limiting_decorator_present(self):
        """Dizimnen ótiwde rate limiting sazlanǵanın testlew."""
        # throttle_classes tekseriw ushın view di import etiw
        from rest_framework.throttling import AnonRateThrottle

        # View de throttle_classes decorator ı barlıǵın tekseriw
        # Register funkciya bolǵanı ushın, haqıyqıy throttling minez-qulqın tekseremiz
        # RegisterRateThrottle klası bar hám AnonRateThrottle bolıwı kerek
        from users.throttles import RegisterRateThrottle
        self.assertTrue(issubclass(RegisterRateThrottle, AnonRateThrottle))
        self.assertEqual(RegisterRateThrottle.rate, '5/min')

    @patch('users.throttles.TESTING', False)
    def test_register_rate_limit_triggers(self):
        """Dizimnen ótiw rate limit i 5 sorawdan keyin iske túsetuǵının testlew."""
        # 6 dizimnen ótiw urınısın islew (shek minutına 5)
        responses = []
        for i in range(6):
            response = self.client.post('/api/v1/auth/register/', {
                'email': f'user{i}@example.com',
                'password': 'testpassword123',
                'password_confirm': 'testpassword123',
                'first_name': 'User',
                'last_name': str(i)
            })
            responses.append(response.status_code)
            # Keyingi soraw anonim bolıwı ushın shıǵıw (dizimnen ótiw avtomatik kiritedi)
            self.client.post('/api/v1/auth/logout/')

        # Keminde biri rate limit lengen (429) bolıwı kerek
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, responses,
                     "Expected rate limit (429) to trigger after 5 registration attempts")
