"""
Izlew endpoint inde rate limit ushın testler.
"""
from django.test import TestCase, Client
from rest_framework import status
from unittest.mock import patch


class SearchRateLimitingTest(TestCase):
    """Izlew endpoint i rate limit i ushın testler - hár IP ge minutına 100 soraw."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = Client()

    def test_search_endpoint_works(self):
        """Izlew endpoint i islewin testlew."""
        response = self.client.get('/api/v1/properties/search/')

        # Jaramlı izlew ushın 200 qaytarıwı kerek
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    @patch('properties.views.TESTING', False)
    def test_search_rate_limit_triggers(self):
        """Izlew rate limit i 100 sorawdan keyin iske túsetuǵının testlew."""
        # 101 izlew sorawın islew (shek minutına 100)
        responses = []
        for i in range(101):
            response = self.client.get('/api/v1/properties/search/')
            responses.append(response.status_code)

        # Keminde biri rate limit lengen (429) bolıwı kerek
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, responses,
                     "Expected rate limit (429) to trigger after 100 search requests")
