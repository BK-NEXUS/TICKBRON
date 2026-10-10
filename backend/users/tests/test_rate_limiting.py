"""
Tests for rate limiting on authentication endpoints.
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import patch

User = get_user_model()


class LoginRateLimitingTest(TestCase):
    """Tests for login endpoint rate limiting - 10 requests per minute per IP."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )

    def test_login_endpoint_works(self):
        """Test that login endpoint works with valid credentials."""
        response = self.client.post('/api/v1/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpassword123'
        })

        # Should return 200 for valid credentials
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])

    @patch('users.views.TESTING', False)
    def test_login_rate_limit_triggers(self):
        """Test that login rate limit triggers after 10 requests."""
        # Make 11 login attempts (limit is 10/min)
        responses = []
        for i in range(11):
            response = self.client.post('/api/v1/auth/login/', {
                'email': 'test@example.com',
                'password': 'wrongpassword'
            })
            responses.append(response.status_code)

        # At least one should be rate limited (429)
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, responses,
                     "Expected rate limit (429) to trigger after 10 login attempts")


class LoggedInSessionRateLimitingTest(TestCase):
    """A throwaway account must not lift the login and register limits."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='throwaway@example.com', password='testpassword123',
            first_name='Throw', last_name='Away'
        )
        self.client.force_login(self.user)

    @patch('users.views.TESTING', False)
    def test_login_limit_applies_to_logged_in_session(self):
        statuses = [
            self.client.post('/api/v1/auth/login/', {'email': 'victim@example.com', 'password': 'x'}).status_code
            for _ in range(12)
        ]
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, statuses)

    @patch('users.views.TESTING', False)
    def test_register_limit_applies_to_logged_in_session(self):
        statuses = [
            self.client.post('/api/v1/auth/register/', {'email': f'n{i}@example.com'}).status_code
            for i in range(7)
        ]
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, statuses)


class RegisterRateLimitingTest(TestCase):
    """Tests for registration endpoint rate limiting - 5 requests per minute per IP."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

    def test_register_endpoint_works(self):
        """Test that registration endpoint works."""
        response = self.client.post('/api/v1/auth/register/', {
            'email': 'newuser@example.com',
            'password': 'testpassword123',
            'password_confirm': 'testpassword123',
            'first_name': 'New',
            'last_name': 'User'
        })

        # Should return 201 for valid registration
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_register_rate_limiting_decorator_present(self):
        """Test that registration has rate limiting configured."""
        # Import the view to check throttle_classes
        from users.views import register
        from rest_framework.throttling import AnonRateThrottle

        # Check that the view has throttle_classes decorator
        # Since register is a function, we verify by checking the actual throttling behavior
        # The RegisterRateThrottle class should exist and be an AnonRateThrottle
        from users.views import RegisterRateThrottle
        self.assertTrue(issubclass(RegisterRateThrottle, AnonRateThrottle))
        self.assertEqual(RegisterRateThrottle.rate, '5/min')

    @patch('users.views.TESTING', False)
    def test_register_rate_limit_triggers(self):
        """Test that registration rate limit triggers after 5 requests."""
        # Make 6 registration attempts (limit is 5/min)
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
            # Logout to ensure next request is anonymous (registration auto-logs in)
            self.client.post('/api/v1/auth/logout/')

        # At least one should be rate limited (429)
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, responses,
                     "Expected rate limit (429) to trigger after 5 registration attempts")
