"""
Tests for the partner room inventory API (3.4, audit #31).

RoomInventory is the room type's real, shared physical room count (the booking engine
locks and updates it since 3.3); DateInventory (still at /partner/inventory/) keeps only
the price and each rate plan's own rules (open/closed, min/max stay).
"""
from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from properties.models import Property, PropertyType, RoomType, RoomInventory
from permissions.models import Role
from users.models import User


class PartnerRoomInventoryTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner',
            defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )

        self.hotel_owner = User.objects.create_user(
            email='hotelowner@example.com', password='testpassword123',
            first_name='John', last_name='Doe', role=self.hotel_owner_role,
        )

        self.property_type = PropertyType.objects.create(
            name='Apartment', slug='apartment', description='Apartment property type'
        )

        self.property = Property.objects.create(
            owner=self.hotel_owner, property_type=self.property_type, status='draft',
            max_guests=4, bedrooms=2, bathrooms=1, address_line1='123 Main St',
            city='Tashkent', country='Uzbekistan', base_price=100.00, currency='USD',
        )

        self.room_type = RoomType.objects.create(
            property=self.property, name='Standard Room', slug='standard-room',
            base_occupancy=2, max_occupancy=4, base_price=100.00, currency='USD', total_rooms=5,
        )

        self.row = RoomInventory.objects.create(
            room_type=self.room_type, date=date.today(), available_rooms=5, booked_rooms=0,
        )

    def test_hotel_owner_can_list_own_room_inventory(self):
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/room-inventory/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.row.id)
        self.assertIn('remaining_rooms', results[0])
        self.assertEqual(results[0]['remaining_rooms'], 5)

    def test_hotel_owner_can_create_room_inventory(self):
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'room_type': self.room_type.id,
            'date': date.today() + timedelta(days=1),
            'available_rooms': 4,
            'is_available': True,
        }
        response = self.client.post('/api/v1/partner/room-inventory/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(RoomInventory.objects.count(), 2)

    def test_available_rooms_cannot_exceed_room_type_total(self):
        """The model enforces this in clean(); DRF never calls it, so the serializer must too."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'room_type': self.room_type.id,
            'date': date.today() + timedelta(days=2),
            'available_rooms': 6,  # room_type.total_rooms is 5
        }
        response = self.client.post('/api/v1/partner/room-inventory/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('available_rooms', str(response.data))
        self.assertEqual(RoomInventory.objects.count(), 1)

    def test_hotel_owner_cannot_modify_booked_rooms(self):
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.patch(
            f'/api/v1/partner/room-inventory/{self.row.id}/', {'booked_rooms': 2}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.row.refresh_from_db()
        self.assertEqual(self.row.booked_rooms, 0)  # read-only, should remain unchanged

    def test_hotel_owner_cannot_create_room_inventory_for_other_property(self):
        other_owner = User.objects.create_user(
            email='other-owner@example.com', password='testpassword123', role=self.hotel_owner_role,
        )
        other_property = Property.objects.create(
            owner=other_owner, property_type=self.property_type, status='draft',
            max_guests=2, bedrooms=1, bathrooms=1, address_line1='456 Oak Ave',
            city='Samarkand', country='Uzbekistan', base_price=50.00, currency='USD',
        )
        other_room_type = RoomType.objects.create(
            property=other_property, name='Other Room', slug='other-room',
            base_occupancy=2, max_occupancy=2, base_price=50.00, currency='USD', total_rooms=2,
        )

        self.client.force_authenticate(user=self.hotel_owner)
        data = {'room_type': other_room_type.id, 'date': date.today(), 'available_rooms': 1}
        response = self.client.post('/api/v1/partner/room-inventory/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_hotel_owner_never_sees_another_owners_room_inventory(self):
        other_owner = User.objects.create_user(
            email='other-owner2@example.com', password='testpassword123', role=self.hotel_owner_role,
        )
        self.client.force_authenticate(user=other_owner)
        response = self.client.get('/api/v1/partner/room-inventory/')

        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 0)

    def test_room_type_and_date_range_filters(self):
        other_room_type = RoomType.objects.create(
            property=self.property, name='Deluxe Room', slug='deluxe-room',
            base_occupancy=2, max_occupancy=2, base_price=150.00, currency='USD', total_rooms=2,
        )
        RoomInventory.objects.create(
            room_type=other_room_type, date=date.today(), available_rooms=2, booked_rooms=0,
        )
        for offset in range(1, 5):
            RoomInventory.objects.create(
                room_type=self.room_type, date=date.today() + timedelta(days=offset),
                available_rooms=5, booked_rooms=0,
            )

        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/room-inventory/', {
            'room_type': self.room_type.id,
            'date_from': (date.today() + timedelta(days=1)).isoformat(),
            'date_to': (date.today() + timedelta(days=2)).isoformat(),
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertTrue(all(row['room_type'] == self.room_type.id for row in response.data['results']))

    def test_unauthenticated_user_cannot_access(self):
        response = self.client.get('/api/v1/partner/room-inventory/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
