"""
Property search with a date range (E2E BUG 1: check_in/check_out returned 500).
"""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from properties.models import Property, PropertyTranslation, PropertyType
from users.models import User

SEARCH_URL = '/api/v1/properties/search/'


class TestSearchWithDates(TestCase):
    def setUp(self):
        owner = User.objects.create_user(email='owner@example.com', password='x')
        hotel = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.property = Property.objects.create(
            owner=owner, property_type=hotel, status='active', max_guests=2, bedrooms=1, bathrooms=1,
            address_line1='1 Main St', city='Tashkent', country='Uzbekistan',
            base_price=Decimal('60.00'), currency='USD',
        )
        PropertyTranslation.objects.create(property=self.property, language='en', name='Test Hotel', description='x')
        self.client = APIClient()

    def test_search_with_check_in_and_check_out_returns_results(self):
        check_in = timezone.localdate() + timedelta(days=3)
        response = self.client.get(SEARCH_URL, {
            'destination': 'Tashkent', 'check_in': str(check_in), 'check_out': str(check_in + timedelta(days=2)),
        })

        assert response.status_code == 200, response.content
        assert [result['id'] for result in response.data['results']] == [self.property.id]

    def test_check_out_before_check_in_is_a_400(self):
        check_in = timezone.localdate() + timedelta(days=3)
        response = self.client.get(SEARCH_URL, {
            'destination': 'Tashkent', 'check_in': str(check_in), 'check_out': str(check_in - timedelta(days=1)),
        })

        assert response.status_code == 400

    def test_search_without_dates_still_works(self):
        response = self.client.get(SEARCH_URL, {'destination': 'Tashkent'})

        assert response.status_code == 200
        assert response.data['count'] == 1
