"""
Property rating scores are public (E2E BUG 9: anonymous visitors got 403 and a red error block).
"""
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Review
from properties.models import Property, PropertyType
from users.models import User

SCORES_URL = '/api/v1/me/reviews/property_scores/'


class TestPublicPropertyScores(TestCase):
    def setUp(self):
        owner = User.objects.create_user(email='owner@example.com', password='x')
        self.guest = User.objects.create_user(email='guest@example.com', password='x')
        hotel = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.property = Property.objects.create(
            owner=owner, property_type=hotel, status='active', max_guests=2, bedrooms=1, bathrooms=1,
            address_line1='1 Main St', city='Tashkent', country='Uzbekistan',
            base_price=Decimal('60.00'), currency='USD',
        )
        Review.objects.create(user=self.guest, property=self.property, overall_rating=4, status='approved')
        Review.objects.create(user=owner, property=self.property, overall_rating=1, status='pending')
        self.client = APIClient()

    def test_anonymous_visitor_gets_the_scores(self):
        response = self.client.get(SCORES_URL, {'property_id': self.property.id})

        assert response.status_code == 200
        # Only approved reviews count
        assert response.data['total_reviews'] == 1
        assert response.data['average_rating'] == 4

    def test_scores_are_read_only(self):
        response = self.client.post(SCORES_URL, {'property_id': self.property.id})

        assert response.status_code in (401, 403, 405)

    def test_review_list_still_requires_login(self):
        response = self.client.get('/api/v1/me/reviews/')

        assert response.status_code in (401, 403)
