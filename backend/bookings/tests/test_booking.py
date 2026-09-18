"""
Tests for TICKBRON booking engine with transaction-safe inventory locking.
"""
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from datetime import date, timedelta
from users.models import User
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory
from bookings.models import Booking, BookingItem
from bookings.serializers import BookingCreateSerializer, BookingCancelSerializer
from rest_framework.test import APIRequestFactory
from unittest.mock import Mock


class BookingModelTests(TestCase):
    """Test cases for Booking model."""
    
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
        
        # Create date inventory for test dates
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
    
    def test_booking_creation_success(self):
        """Test successful booking creation with inventory locking."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        self.assertIsNotNone(booking)
        self.assertEqual(booking.guest, self.user)
        self.assertEqual(booking.property, self.property)
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.payment_status, 'pending')
        self.assertEqual(booking.number_of_nights, 2)
        self.assertEqual(booking.guest_count, 2)
        self.assertEqual(booking.total_price, Decimal('200.00'))
        self.assertIsNotNone(booking.confirmation_code)
        
        # Check booking item was created
        self.assertEqual(booking.booking_items.count(), 1)
        booking_item = booking.booking_items.first()
        self.assertEqual(booking_item.room_type, self.room_type)
        self.assertEqual(booking_item.rate_plan, self.rate_plan)
        self.assertEqual(booking_item.number_of_rooms, 1)
        
        # Check inventory was updated
        inventory_records = DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        )
        for inventory in inventory_records:
            self.assertEqual(inventory.booked_rooms, 1)
    
    def test_booking_creation_insufficient_inventory(self):
        """Test booking creation fails when inventory is insufficient."""
        # Set booked_rooms to available_rooms
        DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        ).update(booked_rooms=5)
        
        with self.assertRaises(ValidationError) as context:
            Booking.create_booking(
                guest=self.user,
                property_obj=self.property,
                room_type=self.room_type,
                rate_plan=self.rate_plan,
                check_in=self.check_in,
                check_out=self.check_out,
                guest_count=2
            )
        
        self.assertIn('availability', context.exception.message_dict)
    
    def test_booking_creation_date_unavailable(self):
        """Test booking creation fails when date is unavailable."""
        # Set is_available to False
        DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date=self.check_in
        ).update(is_available=False)
        
        with self.assertRaises(ValidationError) as context:
            Booking.create_booking(
                guest=self.user,
                property_obj=self.property,
                room_type=self.room_type,
                rate_plan=self.rate_plan,
                check_in=self.check_in,
                check_out=self.check_out,
                guest_count=2
            )
        
        self.assertIn('availability', context.exception.message_dict)
    
    def test_booking_creation_min_nights_violation(self):
        """Test booking creation fails when min nights requirement is violated."""
        # Update rate plan min_nights
        self.rate_plan.min_nights = 3
        self.rate_plan.save()
        
        with self.assertRaises(ValidationError) as context:
            Booking.create_booking(
                guest=self.user,
                property_obj=self.property,
                room_type=self.room_type,
                rate_plan=self.rate_plan,
                check_in=self.check_in,
                check_out=self.check_out,
                guest_count=2
            )
        
        self.assertIn('check_in', context.exception.message_dict)
    
    def test_booking_creation_max_nights_violation(self):
        """Test booking creation fails when max nights requirement is violated."""
        # Update rate plan max_nights
        self.rate_plan.max_nights = 1
        self.rate_plan.save()
        
        with self.assertRaises(ValidationError) as context:
            Booking.create_booking(
                guest=self.user,
                property_obj=self.property,
                room_type=self.room_type,
                rate_plan=self.rate_plan,
                check_in=self.check_in,
                check_out=self.check_out,
                guest_count=2
            )
        
        self.assertIn('check_in', context.exception.message_dict)
    
    def test_booking_creation_invalid_date_range(self):
        """Test booking creation fails with invalid date range."""
        with self.assertRaises(ValidationError) as context:
            Booking.create_booking(
                guest=self.user,
                property_obj=self.property,
                room_type=self.room_type,
                rate_plan=self.rate_plan,
                check_in=self.check_out,
                check_out=self.check_in,
                guest_count=2
            )
        
        self.assertIn('check_out', context.exception.message_dict)
    
    def test_double_booking_prevention(self):
        """Test that double booking is prevented with concurrent requests."""
        # Create first booking
        first_booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        # Refresh inventory to see the updated booked_rooms
        DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        ).update(available_rooms=1)  # Only 1 room available total
        
        # Try to create second booking for same dates (should fail)
        with self.assertRaises(ValidationError) as context:
            Booking.create_booking(
                guest=self.user,
                property_obj=self.property,
                room_type=self.room_type,
                rate_plan=self.rate_plan,
                check_in=self.check_in,
                check_out=self.check_out,
                guest_count=2
            )
        
        self.assertIn('availability', context.exception.message_dict)
    
    def test_booking_cancellation_success(self):
        """Test successful booking cancellation with inventory restoration."""
        # Create booking
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        # Cancel booking
        booking.cancel_booking(cancellation_reason='Test cancellation')
        
        # Check booking status
        self.assertEqual(booking.status, 'cancelled')
        self.assertIsNotNone(booking.cancelled_at)
        self.assertEqual(booking.cancellation_reason, 'Test cancellation')
        
        # Check inventory was restored
        inventory_records = DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        )
        for inventory in inventory_records:
            self.assertEqual(inventory.booked_rooms, 0)
    
    def test_booking_cancellation_invalid_status(self):
        """Test booking cancellation fails for invalid status."""
        # Create booking
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        # Set status to cancelled
        booking.status = 'cancelled'
        booking.save()
        
        # Try to cancel again (should fail)
        with self.assertRaises(ValidationError) as context:
            booking.cancel_booking(cancellation_reason='Test cancellation')
        
        self.assertIn('status', context.exception.message_dict)
    
    def test_confirmation_code_generation(self):
        """Test confirmation code generation is unique."""
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
        
        self.assertNotEqual(booking1.confirmation_code, booking2.confirmation_code)
        self.assertEqual(len(booking1.confirmation_code), 8)
        self.assertEqual(len(booking2.confirmation_code), 8)


class BookingSerializerTests(TestCase):
    """Test cases for booking serializers."""
    
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
        
        # Create mock request
        self.factory = APIRequestFactory()
        self.request = self.factory.post('/api/v1/bookings/')
        self.request.user = self.user
    
    def test_booking_create_serializer_valid(self):
        """Test booking create serializer with valid data."""
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2,
            'special_requests': 'Late check-in requested'
        }
        
        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        
        booking = serializer.save()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.guest, self.user)
        self.assertEqual(booking.status, 'pending')
    
    def test_booking_create_serializer_invalid_date_range(self):
        """Test booking create serializer with invalid date range."""
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_out.strftime('%Y-%m-%d'),
            'check_out': self.check_in.strftime('%Y-%m-%d'),
            'guest_count': 2
        }
        
        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('check_out', serializer.errors)
    
    def test_booking_create_serializer_invalid_property(self):
        """Test booking create serializer with invalid property."""
        data = {
            'property_id': 99999,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2
        }
        
        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('property_id', serializer.errors)
    
    def test_booking_create_serializer_exceeds_max_occupancy(self):
        """Test booking create serializer when guest count exceeds max occupancy."""
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 10  # Exceeds max_occupancy of 4
        }
        
        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('guest_count', serializer.errors)
    
    def test_booking_cancel_serializer_valid(self):
        """Test booking cancel serializer with valid data."""
        # Create booking
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
        
        serializer = BookingCancelSerializer(
            booking,
            data=data,
            partial=True,
            context={'booking': booking}
        )
        self.assertTrue(serializer.is_valid())
        
        updated_booking = serializer.save()
        self.assertEqual(updated_booking.status, 'cancelled')
        self.assertEqual(updated_booking.cancellation_reason, 'Test cancellation')
    
    def test_booking_cancel_serializer_invalid_status(self):
        """Test booking cancel serializer with invalid status."""
        # Create booking
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        # Set status to cancelled
        booking.status = 'cancelled'
        booking.save()
        
        data = {
            'cancellation_reason': 'Test cancellation'
        }
        
        serializer = BookingCancelSerializer(
            booking,
            data=data,
            partial=True,
            context={'booking': booking}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)


class TransactionSafetyTests(TestCase):
    """Test cases for transaction safety and concurrency."""
    
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
        
        # Create date inventory with limited availability
        self.check_in = date.today() + timedelta(days=10)
        self.check_out = date.today() + timedelta(days=12)
        
        current_date = self.check_in
        while current_date < self.check_out:
            DateInventory.objects.create(
                rate_plan=self.rate_plan,
                date=current_date,
                available_rooms=1,  # Only 1 room available
                booked_rooms=0,
                price=Decimal('100.00'),
                currency='USD',
                is_available=True
            )
            current_date += timedelta(days=1)
    
    def test_transaction_rollback_on_error(self):
        """Test that transaction rolls back on error."""
        initial_booked_count = DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        ).first().booked_rooms
        
        # Try to create booking with invalid data (should rollback)
        try:
            with transaction.atomic():
                # Create booking
                booking = Booking.create_booking(
                    guest=self.user,
                    property_obj=self.property,
                    room_type=self.room_type,
                    rate_plan=self.rate_plan,
                    check_in=self.check_in,
                    check_out=self.check_out,
                    guest_count=2
                )
                
                # Force an error to test rollback
                raise ValueError("Simulated error")
        except ValueError:
            pass
        
        # Check that inventory was not updated (transaction rolled back)
        final_booked_count = DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        ).first().booked_rooms
        
        self.assertEqual(initial_booked_count, final_booked_count)
    
    def test_inventory_consistency_after_successful_booking(self):
        """Test that inventory remains consistent after successful booking."""
        # Get initial inventory state
        initial_inventory = list(DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        ))
        
        # Create booking
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        # Check inventory consistency
        final_inventory = list(DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        ))
        
        for initial, final in zip(initial_inventory, final_inventory):
            self.assertEqual(final.booked_rooms, initial.booked_rooms + 1)
            self.assertEqual(final.available_rooms, initial.available_rooms)
            self.assertEqual(final.remaining_rooms, initial.remaining_rooms - 1)