"""
Tests for TICKBRON booking views and API endpoints.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from users.models import User
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory
from bookings.models import Booking, BookingItem


class BookingViewTests(APITestCase):
    """Test cases for booking views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )
        
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            status='active',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Test St',
            city='Test City',
            country='Test Country',
            base_price=Decimal('100.00'),
            currency='USD'
        )
        
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('100.00'),
            currency='USD',
            total_rooms=5
        )
        
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            base_price=Decimal('100.00'),
            currency='USD',
            min_nights=1,
            max_nights=30,
            is_active=True
        )
        
        # Create date inventory
        self.check_in = date.today() + timedelta(days=10)
        self.check_out = date.today() + timedelta(days=12)
        
        current_date = self.check_in
        while current_date < self.check_out:
            DateInventory.objects.create(
                rate_plan=self.rate_plan,
                date=current_date,
                available_rooms=5,
                booked_rooms=0,
                price=Decimal('100.00'),
                currency='USD',
                is_available=True
            )
            current_date += timedelta(days=1)
    
    def test_create_booking_authenticated(self):
        """Test creating booking as authenticated user."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2,
            'special_requests': 'Late check-in requested'
        }
        
        response = self.client.post('/api/v1/bookings/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('confirmation_code', response.data)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['guest_count'], 2)
    
    def test_create_booking_unauthenticated(self):
        """Test creating booking as unauthenticated user."""
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2
        }
        
        response = self.client.post('/api/v1/bookings/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_bookings_authenticated(self):
        """Test listing bookings as authenticated user."""
        # Create a booking
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/bookings/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['confirmation_code'], booking.confirmation_code)
    
    def test_list_bookings_unauthenticated(self):
        """Test listing bookings as unauthenticated user."""
        response = self.client.get('/api/v1/bookings/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_retrieve_booking_authenticated(self):
        """Test retrieving a specific booking as authenticated user."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/bookings/{booking.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['confirmation_code'], booking.confirmation_code)
    
    def test_retrieve_booking_unauthenticated(self):
        """Test retrieving a specific booking as unauthenticated user."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        response = self.client.get(f'/api/v1/bookings/{booking.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cancel_booking_authenticated(self):
        """Test cancelling a booking as authenticated user."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        self.client.force_authenticate(user=self.user)
        
        data = {
            'cancellation_reason': 'Test cancellation'
        }
        
        response = self.client.post(f'/api/v1/bookings/{booking.id}/cancel/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'cancelled')
        self.assertEqual(response.data['cancellation_reason'], 'Test cancellation')
    
    def test_cancel_booking_unauthenticated(self):
        """Test cancelling a booking as unauthenticated user."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        data = {
            'cancellation_reason': 'Test cancellation'
        }
        
        response = self.client.post(f'/api/v1/bookings/{booking.id}/cancel/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_booking_invalid_date_range(self):
        """Test creating booking with invalid date range."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_out.strftime('%Y-%m-%d'),
            'check_out': self.check_in.strftime('%Y-%m-%d'),
            'guest_count': 2
        }
        
        response = self.client.post('/api/v1/bookings/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('check_out', response.data['details'])
    
    def test_create_booking_insufficient_inventory(self):
        """Test creating booking when inventory is insufficient."""
        # Set available_rooms to 0 to simulate no availability
        DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        ).update(available_rooms=0, booked_rooms=0)
        
        self.client.force_authenticate(user=self.user)
        
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2
        }
        
        response = self.client.post('/api/v1/bookings/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check that the error contains availability information
        self.assertIn('availability', str(response.data).lower())
    
    def test_filter_bookings_by_status(self):
        """Test filtering bookings by status."""
        # Create multiple bookings
        booking1 = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        # Create inventory for second booking dates
        check_in2 = date.today() + timedelta(days=20)
        check_out2 = date.today() + timedelta(days=22)
        
        current_date = check_in2
        while current_date < check_out2:
            DateInventory.objects.create(
                rate_plan=self.rate_plan,
                date=current_date,
                available_rooms=5,
                booked_rooms=0,
                price=Decimal('100.00'),
                currency='USD',
                is_available=True
            )
            current_date += timedelta(days=1)
        
        booking2 = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=check_in2,
            check_out=check_out2,
            guest_count=2
        )
        
        # Cancel one booking
        booking1.cancel_booking('Test cancellation')
        
        self.client.force_authenticate(user=self.user)
        
        # Filter by status
        response = self.client.get('/api/v1/bookings/?status=cancelled')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'cancelled')