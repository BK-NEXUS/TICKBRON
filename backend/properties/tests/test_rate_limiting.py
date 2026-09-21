"""
Tests for rate limiting on search endpoint.
"""
import pytest
from django.test import TestCase, Client
from rest_framework import status
from unittest.mock import patch


class SearchRateLimitingTest(TestCase):
    """Tests for search endpoint rate limiting - 100 requests per minute per IP."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

    def test_search_endpoint_works(self):
        """Test that search endpoint works."""
        response = self.client.get('/api/v1/properties/search/')

        # Should return 200 for valid search
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    @patch('properties.views.TESTING', False)
    def test_search_rate_limit_triggers(self):
        """Test that search rate limit triggers after 100 requests."""
        # Make 101 search requests (limit is 100/min)
        responses = []
        for i in range(101):
            response = self.client.get('/api/v1/properties/search/')
            responses.append(response.status_code)

        # At least one should be rate limited (429)
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, responses,
                     "Expected rate limit (429) to trigger after 100 search requests")
