"""
Tests for property availability API endpoint.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from properties.models import (
    Property, PropertyType, PropertyAmenity,
    Amenity, AmenityCategory,
    RoomType, RoomAmenity, RatePlan, DateInventory
)
from datetime import date, timedelta

User = get_user_model()


class PropertyAvailabilityEndpointTest(TestCase):
    """Test cases for property availability API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )
        
        self.amenity_category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen',
            description='Kitchen amenities'
        )
        
        self.wifi_amenity = Amenity.objects.create(
            category=self.amenity_category,
            name='WiFi',
            slug='wifi',
            description='Wireless internet',
            is_searchable=True
        )
        
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            status='active',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            latitude=41.2995,
            longitude=69.2401,
            base_price=50.00,
            currency='USD'
        )
        
        # Add amenities to property
        PropertyAmenity.objects.create(
            property=self.property,
            amenity=self.wifi_amenity,
            is_available=True
        )
        
        # Add room type with rate plans
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            description='Comfortable standard room',
            base_occupancy=2,
            max_occupancy=2,
            base_price=50.00,
            currency='USD',
            total_rooms=5
        )
        
        # Add room amenities
        RoomAmenity.objects.create(
            room_type=self.room_type,
            amenity=self.wifi_amenity,
            is_available=True
        )
        
        # Add rate plan
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            description='Standard rate with flexible cancellation',
            base_price=50.00,
            currency='USD',
            min_nights=1,
            is_active=True
        )
        
        # Add date inventory for next 7 days
        today = date.today()
        for i in range(1, 8):
            inventory_date = today + timedelta(days=i)
            DateInventory.objects.create(
                rate_plan=self.rate_plan,
                date=inventory_date,
                available_rooms=5,
                booked_rooms=0,
                price=50.00,
                currency='USD',
                is_available=True
            )
        
        # Add another room type
        self.room_type_2 = RoomType.objects.create(
            property=self.property,
            name='Deluxe Room',
            slug='deluxe-room',
            description='Spacious deluxe room',
            base_occupancy=2,
            max_occupancy=3,
            base_price=80.00,
            currency='USD',
            total_rooms=3
        )
        
        # Add rate plan for second room type
        self.rate_plan_2 = RatePlan.objects.create(
            room_type=self.room_type_2,
            name='Deluxe Rate',
            slug='deluxe-rate',
            rate_type='standard',
            description='Deluxe rate with extra amenities',
            base_price=80.00,
            currency='USD',
            min_nights=1,
            is_active=True
        )
        
        # Add date inventory for second rate plan
        for i in range(1, 8):
            inventory_date = today + timedelta(days=i)
            DateInventory.objects.create(
                rate_plan=self.rate_plan_2,
                date=inventory_date,
                available_rooms=3,
                booked_rooms=0,
                price=80.00,
                currency='USD',
                is_available=True
            )
    
    def test_availability_success(self):
        """Test successful availability request."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['id'], self.property.id)
        self.assertIn('room_types', response.data)
    
    def test_availability_includes_property_info(self):
        """Test that availability includes basic property information."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['city'], 'Tashkent')
        self.assertEqual(response.data['country'], 'Uzbekistan')
        self.assertEqual(response.data['max_guests'], 4)
        self.assertEqual(str(response.data['base_price']), '50.00')
    
    def test_availability_includes_room_types(self):
        """Test that availability includes room types."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('room_types', response.data)
        room_types = response.data['room_types']
        self.assertGreater(len(room_types), 0)
        
        # Check room type structure
        first_room_type = room_types[0]
        self.assertIn('id', first_room_type)
        self.assertIn('name', first_room_type)
        self.assertIn('base_occupancy', first_room_type)
        self.assertIn('max_occupancy', first_room_type)
        self.assertIn('rate_plans', first_room_type)
    
    def test_availability_includes_rate_plans(self):
        """Test that room types include rate plans."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        
        self.assertIn('rate_plans', first_room_type)
        rate_plans = first_room_type['rate_plans']
        self.assertGreater(len(rate_plans), 0)
        
        # Check rate plan structure
        first_rate_plan = rate_plans[0]
        self.assertIn('id', first_rate_plan)
        self.assertIn('name', first_rate_plan)
        self.assertIn('rate_type', first_rate_plan)
        self.assertIn('base_price', first_rate_plan)
        self.assertIn('min_nights', first_rate_plan)
    
    def test_availability_includes_date_inventory(self):
        """Test that rate plans include date inventory."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        rate_plans = first_room_type['rate_plans']
        first_rate_plan = rate_plans[0]
        
        self.assertIn('date_inventory', first_rate_plan)
        date_inventory = first_rate_plan['date_inventory']
        self.assertGreater(len(date_inventory), 0)
        
        # Check date inventory structure
        first_inventory = date_inventory[0]
        self.assertIn('date', first_inventory)
        self.assertIn('available_rooms', first_inventory)
        self.assertIn('booked_rooms', first_inventory)
        self.assertIn('remaining_rooms', first_inventory)
        self.assertIn('price', first_inventory)
        self.assertIn('is_available', first_inventory)
    
    def test_availability_with_date_range(self):
        """Test availability with date range parameters."""
        today = date.today()
        check_in = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        check_out = (today + timedelta(days=3)).strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': check_in, 'check_out': check_out}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that date inventory is filtered by date range
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        rate_plans = first_room_type['rate_plans']
        first_rate_plan = rate_plans[0]
        date_inventory = first_rate_plan['date_inventory']
        
        # Should only include dates within the range
        self.assertLessEqual(len(date_inventory), 3)
    
    def test_availability_with_only_check_in(self):
        """Test availability with only check_in parameter."""
        today = date.today()
        check_in = (today + timedelta(days=2)).strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': check_in}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that date inventory is filtered from check_in onwards
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        rate_plans = first_room_type['rate_plans']
        first_rate_plan = rate_plans[0]
        date_inventory = first_rate_plan['date_inventory']
        
        # Should only include dates from check_in onwards
        self.assertGreater(len(date_inventory), 0)
    
    def test_availability_invalid_date_format(self):
        """Test availability with invalid date format."""
        response = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': 'invalid-date', 'check_out': '2024-01-10'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_availability_invalid_date_range(self):
        """Test availability with invalid date range (check_out before check_in)."""
        today = date.today()
        check_in = (today + timedelta(days=5)).strftime('%Y-%m-%d')
        check_out = (today + timedelta(days=2)).strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': check_in, 'check_out': check_out}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_availability_property_not_found(self):
        """Test availability with non-existent property ID."""
        response = self.client.get('/api/v1/properties/99999/availability/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_availability_deleted_property(self):
        """Test availability with deleted property."""
        # Soft delete the property
        self.property.is_deleted = True
        self.property.save()
        
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_availability_inactive_property(self):
        """Test availability with inactive property."""
        # Deactivate the property
        self.property.is_active = False
        self.property.save()
        
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_availability_public_access(self):
        """Test that availability endpoint is publicly accessible."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')
        
        # Should work without authentication
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_availability_deterministic_pricing(self):
        """Test that availability pricing is deterministic (same inputs = same outputs)."""
        today = date.today()
        check_in = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        check_out = (today + timedelta(days=3)).strftime('%Y-%m-%d')
        
        # Make the same request twice
        response1 = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': check_in, 'check_out': check_out}
        )
        
        response2 = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': check_in, 'check_out': check_out}
        )
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Compare the responses
        self.assertEqual(response1.data, response2.data)
    
    def test_availability_remaining_rooms_calculation(self):
        """Test that remaining_rooms is calculated correctly."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        rate_plans = first_room_type['rate_plans']
        first_rate_plan = rate_plans[0]
        date_inventory = first_rate_plan['date_inventory']
        
        # Check remaining_rooms calculation
        first_inventory = date_inventory[0]
        expected_remaining = first_inventory['available_rooms'] - first_inventory['booked_rooms']
        self.assertEqual(first_inventory['remaining_rooms'], expected_remaining)
    
    def test_availability_filters_inactive_rate_plans(self):
        """Test that inactive rate plans are filtered out."""
        # Deactivate one rate plan
        self.rate_plan.is_active = False
        self.rate_plan.save()
        
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        rate_plans = first_room_type['rate_plans']
        
        # Should not include the inactive rate plan
        rate_plan_ids = [rp['id'] for rp in rate_plans]
        self.assertNotIn(self.rate_plan.id, rate_plan_ids)
    
    def test_availability_multiple_room_types(self):
        """Test availability with multiple room types."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_types = response.data['room_types']
        
        # Should include both room types
        self.assertEqual(len(room_types), 2)
        room_type_ids = [rt['id'] for rt in room_types]
        self.assertIn(self.room_type.id, room_type_ids)
        self.assertIn(self.room_type_2.id, room_type_ids)
    
    def test_availability_no_date_range(self):
        """Test availability without date range parameters."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return all date inventory
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        rate_plans = first_room_type['rate_plans']
        first_rate_plan = rate_plans[0]
        date_inventory = first_rate_plan['date_inventory']
        
        # Should include all 7 days of inventory
        self.assertEqual(len(date_inventory), 7)