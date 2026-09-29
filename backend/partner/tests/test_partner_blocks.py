"""
Tests for the partner external-booking blocks API (3.5, audit #31 follow-up).
"""
from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from properties.models import Property, PropertyType, RoomType, RoomInventory, RoomBlock
from permissions.models import Role
from users.models import User


class PartnerBlockTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner', defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )
        self.hotel_owner = User.objects.create_user(
            email='hotelowner@example.com', password='testpassword123', role=self.hotel_owner_role,
        )
        self.property_type = PropertyType.objects.create(name='Apartment', slug='apartment-block')
        self.property = Property.objects.create(
            owner=self.hotel_owner, property_type=self.property_type, status='draft',
            max_guests=4, bedrooms=2, bathrooms=1, address_line1='123 Main St',
            city='Tashkent', country='Uzbekistan', base_price=100.00, currency='USD',
        )
        self.room_type = RoomType.objects.create(
            property=self.property, name='Standard Room', slug='standard-room-block',
            base_occupancy=2, max_occupancy=4, base_price=100.00, currency='USD', total_rooms=5,
        )
        self.start = date.today() + timedelta(days=1)
        self.end = self.start + timedelta(days=2)

    def test_hotel_owner_can_create_a_block(self):
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.post('/api/v1/partner/blocks/', {
            'room_type': self.room_type.id, 'date_from': self.start.isoformat(),
            'date_to': self.end.isoformat(), 'rooms': 2, 'note': 'Booking.com',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['created_by'], self.hotel_owner.id)
        row = RoomInventory.objects.get(room_type=self.room_type, date=self.start)
        self.assertEqual(row.available_rooms, 3)

    def test_block_error_names_the_date(self):
        RoomInventory.objects.create(
            room_type=self.room_type, date=self.start, available_rooms=5, booked_rooms=5,
        )
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.post('/api/v1/partner/blocks/', {
            'room_type': self.room_type.id, 'date_from': self.start.isoformat(),
            'date_to': self.end.isoformat(), 'rooms': 1, 'note': 'phone',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(self.start.isoformat(), str(response.data))

    def test_hotel_owner_can_list_own_blocks(self):
        block = RoomBlock.create_block(
            room_type=self.room_type, date_from=self.start, date_to=self.end,
            rooms=1, note='phone', created_by=self.hotel_owner,
        )
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/blocks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual([row['id'] for row in results], [block.id])

    def test_hotel_owner_can_delete_a_block_and_rooms_come_back(self):
        block = RoomBlock.create_block(
            room_type=self.room_type, date_from=self.start, date_to=self.end,
            rooms=2, note='phone', created_by=self.hotel_owner,
        )
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.delete(f'/api/v1/partner/blocks/{block.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        row = RoomInventory.objects.get(room_type=self.room_type, date=self.start)
        self.assertEqual(row.available_rooms, 5)
        self.assertTrue(RoomBlock.objects.get(id=block.id).is_deleted)  # soft-deleted, not gone

    def test_hotel_owner_cannot_see_or_delete_another_owners_block(self):
        other_owner = User.objects.create_user(
            email='other-owner-block@example.com', password='testpassword123', role=self.hotel_owner_role,
        )
        block = RoomBlock.create_block(
            room_type=self.room_type, date_from=self.start, date_to=self.end,
            rooms=1, note='phone', created_by=self.hotel_owner,
        )
        self.client.force_authenticate(user=other_owner)
        list_response = self.client.get('/api/v1/partner/blocks/')
        results = (
            list_response.data.get('results', list_response.data)
            if isinstance(list_response.data, dict) else list_response.data
        )
        self.assertEqual(results, [])
        delete_response = self.client.delete(f'/api/v1/partner/blocks/{block.id}/')
        self.assertEqual(delete_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_hotel_owner_cannot_block_another_owners_room_type(self):
        other_owner = User.objects.create_user(
            email='other-owner-block2@example.com', password='testpassword123', role=self.hotel_owner_role,
        )
        other_property = Property.objects.create(
            owner=other_owner, property_type=self.property_type, status='draft',
            max_guests=2, bedrooms=1, bathrooms=1, address_line1='456 Oak Ave',
            city='Samarkand', country='Uzbekistan', base_price=50.00, currency='USD',
        )
        other_room_type = RoomType.objects.create(
            property=other_property, name='Other Room', slug='other-room-block',
            base_occupancy=2, max_occupancy=2, base_price=50.00, currency='USD', total_rooms=2,
        )
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.post('/api/v1/partner/blocks/', {
            'room_type': other_room_type.id, 'date_from': self.start.isoformat(),
            'date_to': self.end.isoformat(), 'rooms': 1, 'note': 'phone',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_user_cannot_access(self):
        response = self.client.get('/api/v1/partner/blocks/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
