"""
Tests for rate limiting on payment endpoints.
"""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import patch

User = get_user_model()


class PaymentRateLimitingTest(TestCase):
    """Tests for payment initiation endpoint rate limiting - 20 requests per minute per user."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )

        self.client.force_authenticate(user=self.user)

    def test_payment_rate_limiting_decorator_present(self):
        """Test that payment initiation has rate limiting configured."""
        # Import the viewset to check throttle_classes
        from payments.views import PaymentTransactionViewSet
        from rest_framework.throttling import UserRateThrottle

        # Check that the viewset has throttle_classes
        self.assertTrue(hasattr(PaymentTransactionViewSet, 'throttle_classes'))
        self.assertEqual(len(PaymentTransactionViewSet.throttle_classes), 1)

    @patch('payments.views.TESTING', False)
    def test_payment_rate_limit_triggers(self):
        """Test that payment rate limit triggers after 20 requests."""
        # Make 21 payment initiation attempts (limit is 20/min)
        responses = []
        for i in range(21):
            response = self.client.post('/api/v1/payments/transactions/', {
                'booking': 1,  # Invalid booking, but will still hit rate limit
                'amount': 100.00,
                'currency': 'USD',
                'provider': 'payme',
                'payment_method_token': 'test_token',
                'idempotency_key': f'test_key_{i}'
            })
            responses.append(response.status_code)

        # At least one should be rate limited (429)
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, responses,
                     "Expected rate limit (429) to trigger after 20 payment initiation attempts")
