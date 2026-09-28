"""
Partner property cards show the hotel name, not the city (E2E flow E, Phase 2 item 4):
GET /partner/properties/ and /partner/properties/{id}/ return a read-only `name`.
"""
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from permissions.models import Role
from properties.models import Property, PropertyTranslation, PropertyType
from users.models import User

LIST_URL = '/api/v1/partner/properties/'


class TestPartnerPropertyName(TestCase):
    def setUp(self):
        role, _ = Role.objects.get_or_create(
            name='hotel-owner', defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )
        self.owner = User.objects.create_user(email='owner@example.com', password='x', role=role)
        hotel = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.named = Property.objects.create(
            owner=self.owner, property_type=hotel, status='active', max_guests=2,
            address_line1='1 Main St', city='Tashkent', country='Uzbekistan', base_price=Decimal('60.00'),
        )
        PropertyTranslation.objects.create(property=self.named, language='ru', name='Отель Ташкент', description='x')
        PropertyTranslation.objects.create(property=self.named, language='en', name='Hotel Tashkent', description='x')
        self.unnamed = Property.objects.create(
            owner=self.owner, property_type=hotel, status='draft', max_guests=2,
            address_line1='2 Side St', city='Bukhara', country='Uzbekistan', base_price=Decimal('40.00'),
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def test_list_has_the_hotel_name(self):
        response = self.client.get(LIST_URL)
        assert response.status_code == 200
        rows = response.data['results'] if isinstance(response.data, dict) else response.data
        names = {row['id']: row['name'] for row in rows}
        assert names[self.named.id] == 'Hotel Tashkent'
        # Without a translation the name falls back to the address, never empty
        assert names[self.unnamed.id] == self.unnamed.get_full_address()

    def test_detail_has_the_hotel_name(self):
        response = self.client.get(f'{LIST_URL}{self.named.id}/')
        assert response.status_code == 200
        assert response.data['name'] == 'Hotel Tashkent'

    def test_name_is_read_only(self):
        response = self.client.patch(f'{LIST_URL}{self.named.id}/', {'name': 'Hacked'}, format='json')
        assert response.status_code in (200, 400)
        self.named.refresh_from_db()
        assert self.named.display_name() == 'Hotel Tashkent'
