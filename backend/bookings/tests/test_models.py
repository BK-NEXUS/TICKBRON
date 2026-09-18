"""
Tests for TICKBRON booking models.
"""
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta
from users.models import User
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory
from bookings.models import Booking, BookingItem


class BookingModelBasicTests(TestCase):
    """Basic test cases for Booking model."""
    
    def setUp(self):
        """Set up test data."""
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
    
    def test_booking_string_representation(self):
        """Test booking string representation."""
        booking = Booking.objects.create(
            guest=self.user,
            property=self.property,
            status='pending',
            check_in=date.today() + timedelta(days=10),
            check_out=date.today() + timedelta(days=12),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            confirmation_code='TEST1234'
        )
        
        expected_str = f"Booking TEST1234 - {self.property}"
        self.assertEqual(str(booking), expected_str)
    
    def test_booking_item_string_representation(self):
        """Test booking item string representation."""
        booking = Booking.objects.create(
            guest=self.user,
            property=self.property,
            status='pending',
            check_in=date.today() + timedelta(days=10),
            check_out=date.today() + timedelta(days=12),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            confirmation_code='TEST1234'
        )
        
        booking_item = BookingItem.objects.create(
            booking=booking,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )
        
        expected_str = f"TEST1234 - {self.room_type.name}"
        self.assertEqual(str(booking_item), expected_str)
    
    def test_booking_validation_invalid_date_range(self):
        """Test booking validation with invalid date range."""
        booking = Booking(
            guest=self.user,
            property=self.property,
            status='pending',
            check_in=date.today() + timedelta(days=12),
            check_out=date.today() + timedelta(days=10),  # Invalid: check_out before check_in
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            confirmation_code='TEST1234'
        )
        
        with self.assertRaises(ValidationError) as context:
            booking.clean()
        
        self.assertIn('check_out', context.exception.message_dict)
    
    def test_booking_confirmation_code_generation(self):
        """Test that confirmation code is generated automatically."""
        booking = Booking.objects.create(
            guest=self.user,
            property=self.property,
            status='pending',
            check_in=date.today() + timedelta(days=10),
            check_out=date.today() + timedelta(days=12),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD'
        )
        
        self.assertIsNotNone(booking.confirmation_code)
        self.assertEqual(len(booking.confirmation_code), 8)
    
    def test_booking_number_of_nights_calculation(self):
        """Test that number_of_nights is calculated automatically."""
        check_in = date.today() + timedelta(days=10)
        check_out = date.today() + timedelta(days=15)
        
        booking = Booking.objects.create(
            guest=self.user,
            property=self.property,
            status='pending',
            check_in=check_in,
            check_out=check_out,
            guest_count=2,
            total_price=Decimal('500.00'),
            currency='USD'
        )
        
        expected_nights = (check_out - check_in).days
        self.assertEqual(booking.number_of_nights, expected_nights)