"""
Tests for the partner bulk calendar-edit endpoints (3.6/3.7):
POST /partner/room-inventory/bulk/ and POST /partner/inventory/bulk-price/.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from properties.models import (
    DateInventory, Property, PropertyType, RatePlan, RoomInventory, RoomType,
)
from permissions.models import Role
from users.models import User


class PartnerRoomInventoryBulkTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner', defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )
        self.hotel_owner = User.objects.create_user(
            email='hotelowner@example.com', password='testpassword123', role=self.hotel_owner_role,
        )
        self.property_type = PropertyType.objects.create(name='Apartment', slug='apartment-bulk')
        self.property = Property.objects.create(
            owner=self.hotel_owner, property_type=self.property_type, status='draft',
            max_guests=4, bedrooms=2, bathrooms=1, address_line1='123 Main St',
            city='Tashkent', country='Uzbekistan', base_price=100.00, currency='USD',
        )
        self.room_type = RoomType.objects.create(
            property=self.property, name='Standard Room', slug='standard-room-bulk',
            base_occupancy=2, max_occupancy=4, base_price=100.00, currency='USD', total_rooms=5,
        )
        self.start = date.today() + timedelta(days=1)
        self.end = self.start + timedelta(days=2)

    def test_hotel_owner_can_bulk_set_available_rooms(self):
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.post('/api/v1/partner/room-inventory/bulk/', {
            'room_type': self.room_type.id, 'date_from': self.start.isoformat(),
            'date_to': self.end.isoformat(), 'available_rooms': 3,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data), 2)
        for offset in range(2):
            row = RoomInventory.objects.get(room_type=self.room_type, date=self.start + timedelta(days=offset))
            self.assertEqual(row.available_rooms, 3)

    def test_bulk_error_names_the_date(self):
        booked_date = self.start
        RoomInventory.objects.create(room_type=self.room_type, date=booked_date, available_rooms=5, booked_rooms=4)
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.post('/api/v1/partner/room-inventory/bulk/', {
            'room_type': self.room_type.id, 'date_from': self.start.isoformat(),
            'date_to': self.end.isoformat(), 'available_rooms': 2,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(booked_date.isoformat(), str(response.data))

    def test_hotel_owner_cannot_bulk_edit_another_owners_room_type(self):
        other_owner = User.objects.create_user(
            email='other-owner-bulk@example.com', password='testpassword123', role=self.hotel_owner_role,
        )
        other_property = Property.objects.create(
            owner=other_owner, property_type=self.property_type, status='draft',
            max_guests=2, bedrooms=1, bathrooms=1, address_line1='456 Oak Ave',
            city='Samarkand', country='Uzbekistan', base_price=50.00, currency='USD',
        )
        other_room_type = RoomType.objects.create(
            property=other_property, name='Other Room', slug='other-room-bulk',
            base_occupancy=2, max_occupancy=2, base_price=50.00, currency='USD', total_rooms=2,
        )
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.post('/api/v1/partner/room-inventory/bulk/', {
            'room_type': other_room_type.id, 'date_from': self.start.isoformat(),
            'date_to': self.end.isoformat(), 'available_rooms': 1,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_user_cannot_access(self):
        response = self.client.post('/api/v1/partner/room-inventory/bulk/', {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PartnerDateInventoryBulkPriceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner', defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )
        self.hotel_owner = User.objects.create_user(
            email='hotelowner2@example.com', password='testpassword123', role=self.hotel_owner_role,
        )
        self.property_type = PropertyType.objects.create(name='Apartment', slug='apartment-bulkprice')
        self.property = Property.objects.create(
            owner=self.hotel_owner, property_type=self.property_type, status='draft',
            max_guests=4, bedrooms=2, bathrooms=1, address_line1='123 Main St',
            city='Tashkent', country='Uzbekistan', base_price=100.00, currency='USD',
        )
        self.room_type = RoomType.objects.create(
            property=self.property, name='Standard Room', slug='standard-room-bulkprice',
            base_occupancy=2, max_occupancy=4, base_price=100.00, currency='USD', total_rooms=4,
        )
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type, name='Standard Rate', slug='standard-rate-bulkprice', rate_type='standard',
            base_price=100.00, currency='USD', min_nights=1, is_active=True,
        )
        self.start = date.today() + timedelta(days=1)
        self.end = self.start + timedelta(days=2)

    def test_hotel_owner_can_bulk_set_price(self):
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.post('/api/v1/partner/inventory/bulk-price/', {
            'rate_plan': self.rate_plan.id, 'date_from': self.start.isoformat(),
            'date_to': self.end.isoformat(), 'price': '120.00',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data), 2)
        for offset in range(2):
            row = DateInventory.objects.get(rate_plan=self.rate_plan, date=self.start + timedelta(days=offset))
            self.assertEqual(row.price, Decimal('120.00'))

    def test_hotel_owner_cannot_bulk_price_another_owners_rate_plan(self):
        other_owner = User.objects.create_user(
            email='other-owner-bulkprice@example.com', password='testpassword123', role=self.hotel_owner_role,
        )
        other_property = Property.objects.create(
            owner=other_owner, property_type=self.property_type, status='draft',
            max_guests=2, bedrooms=1, bathrooms=1, address_line1='456 Oak Ave',
            city='Samarkand', country='Uzbekistan', base_price=50.00, currency='USD',
        )
        other_room_type = RoomType.objects.create(
            property=other_property, name='Other Room', slug='other-room-bulkprice',
            base_occupancy=2, max_occupancy=2, base_price=50.00, currency='USD', total_rooms=2,
        )
        other_rate_plan = RatePlan.objects.create(
            room_type=other_room_type, name='Other Rate', slug='other-rate-bulkprice', rate_type='standard',
            base_price=50.00, currency='USD', min_nights=1, is_active=True,
        )
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.post('/api/v1/partner/inventory/bulk-price/', {
            'rate_plan': other_rate_plan.id, 'date_from': self.start.isoformat(),
            'date_to': self.end.isoformat(), 'price': '10.00',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_user_cannot_access(self):
        response = self.client.post('/api/v1/partner/inventory/bulk-price/', {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PartnerBlockRoomTypeFilterTests(TestCase):
    """3.6: ?room_type= filters the blocks list (used by the calendar screen)."""

    def setUp(self):
        self.client = APIClient()
        self.hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner', defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )
        self.hotel_owner = User.objects.create_user(
            email='hotelowner3@example.com', password='testpassword123', role=self.hotel_owner_role,
        )
        self.property_type = PropertyType.objects.create(name='Apartment', slug='apartment-blockfilter')
        self.property = Property.objects.create(
            owner=self.hotel_owner, property_type=self.property_type, status='draft',
            max_guests=4, bedrooms=2, bathrooms=1, address_line1='123 Main St',
            city='Tashkent', country='Uzbekistan', base_price=100.00, currency='USD',
        )
        self.room_a = RoomType.objects.create(
            property=self.property, name='Room A', slug='room-a-blockfilter',
            base_occupancy=2, max_occupancy=2, base_price=100.00, currency='USD', total_rooms=3,
        )
        self.room_b = RoomType.objects.create(
            property=self.property, name='Room B', slug='room-b-blockfilter',
            base_occupancy=2, max_occupancy=2, base_price=100.00, currency='USD', total_rooms=3,
        )
        from properties.models import RoomBlock
        start = date.today() + timedelta(days=1)
        self.block_a = RoomBlock.create_block(
            room_type=self.room_a, date_from=start, date_to=start + timedelta(days=1),
            rooms=1, note='phone', created_by=self.hotel_owner,
        )
        self.block_b = RoomBlock.create_block(
            room_type=self.room_b, date_from=start, date_to=start + timedelta(days=1),
            rooms=1, note='phone', created_by=self.hotel_owner,
        )

    def test_room_type_filter(self):
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/blocks/', {'room_type': self.room_a.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual([row['id'] for row in results], [self.block_a.id])
