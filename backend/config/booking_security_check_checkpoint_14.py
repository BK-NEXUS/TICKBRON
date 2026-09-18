"""
Security Review Script for Checkpoint 14 - Booking Expiry, Cancellation, and Inventory Restoration

This script performs a comprehensive security review of the booking expiry implementation
including deterministic state transitions and inventory restoration.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('ALLOWED_HOSTS', 'testserver,localhost,127.0.0.1')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory
from bookings.models import Booking, BookingItem

User = get_user_model()


class BookingExpirySecurityCheck(TestCase):
    """Security checks for booking expiry implementation."""

    def setUp(self):
        """Set up test data for security checks."""
        self.user = User.objects.create_user(
            email='security@example.com',
            password='SecurePassword123!',
            first_name='Security',
            last_name='Test'
        )
        
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='OtherPassword123!',
            first_name='Other',
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
        
        self.client = Client()

    def test_01_expiry_field_is_properly_indexed(self):
        """Test that expiry field is properly indexed for performance."""
        # Check that the model has the expiry field
        from bookings.models import Booking as BookingModel
        booking = BookingModel(
            guest=self.user,
            property=self.property,
            status='pending',
            check_in=self.check_in,
            check_out=self.check_out,
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD'
        )
        self.assertTrue(hasattr(booking, 'expires_at'))
        
        # Check that the field is db_index=True in the model
        field = BookingModel._meta.get_field('expires_at')
        self.assertTrue(field.db_index, "Expiry field should be indexed")

    def test_02_expiry_timestamp_auto_generated(self):
        """Test that expiry timestamp is automatically generated for pending bookings."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        self.assertIsNotNone(booking.expires_at)
        # Check that expiry is approximately 15 minutes from creation
        expected_expiry = booking.created_at + timedelta(minutes=15)
        time_difference = abs((booking.expires_at - expected_expiry).total_seconds())
        self.assertLess(time_difference, 5)  # Allow 5 seconds variance

    def test_03_expiry_only_for_pending_bookings(self):
        """Test that expiry is only set for pending bookings."""
        # Create a pending booking
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        self.assertEqual(booking.status, 'pending')
        self.assertIsNotNone(booking.expires_at)
        
        # Cancel the booking
        booking.cancel_booking('Test cancellation')
        
        # Update to confirmed status (simulating payment)
        booking.status = 'confirmed'
        booking.save()
        
        # Create another booking that goes straight to confirmed
        booking2 = Booking(
            guest=self.user,
            property=self.property,
            status='confirmed',
            payment_status='paid',
            check_in=self.check_in,
            check_out=self.check_out,
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD'
        )
        booking2.save()
        
        # Confirmed bookings should not auto-generate expiry
        self.assertIsNone(booking2.expires_at)

    def test_04_expiry_transaction_safety(self):
        """Test that expiry operations are transaction-safe."""
        from django.db import transaction
        
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        # Get initial inventory state
        initial_inventory = list(DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        ))
        
        # Try to expire with forced rollback
        try:
            with transaction.atomic():
                booking.expire_booking()
                # Force rollback
                raise ValueError("Test rollback")
        except ValueError:
            pass
        
        # Check inventory remains unchanged after rollback
        final_inventory = list(DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        ))
        
        for initial, final in zip(initial_inventory, final_inventory):
            self.assertEqual(initial.booked_rooms, final.booked_rooms)

    def test_05_expiry_inventory_restoration_accuracy(self):
        """Test that expiry accurately restores inventory."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        # Get inventory after booking
        booked_after_booking = DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date=self.check_in
        ).first().booked_rooms
        
        # Expire the booking
        booking.expire_booking()
        
        # Check that inventory was restored
        booked_after_expiry = DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date=self.check_in
        ).first().booked_rooms
        
        self.assertEqual(booked_after_expiry, booked_after_booking - 1)

    def test_06_expiry_status_validation(self):
        """Test that expiry can only happen for pending bookings."""
        # Create and confirm a booking
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        booking.status = 'confirmed'
        booking.save()
        
        # Try to expire confirmed booking (should fail)
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as context:
            booking.expire_booking()
        
        self.assertIn('status', context.exception.message_dict)

    def test_07_expiry_cancellation_reason_integrity(self):
        """Test that expiry sets proper cancellation reason."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        booking.expire_booking()
        
        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(booking.cancellation_reason, 'Booking expired - payment not completed within time limit')
        self.assertIsNotNone(booking.cancelled_at)

    def test_08_deterministic_state_transitions(self):
        """Test that state transitions are deterministic and well-defined."""
        # Test pending -> cancelled (expiry)
        booking1 = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        self.assertEqual(booking1.status, 'pending')
        booking1.expire_booking()
        self.assertEqual(booking1.status, 'cancelled')
        
        # Test pending -> cancelled (user cancellation)
        booking2 = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        self.assertEqual(booking2.status, 'pending')
        booking2.cancel_booking('User cancelled')
        self.assertEqual(booking2.status, 'cancelled')
        
        # Test that cancelled cannot be cancelled again
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            booking1.cancel_booking('Try again')
        
        with self.assertRaises(ValidationError):
            booking1.expire_booking()

    def test_09_process_expired_bookings_safety(self):
        """Test that process_expired_bookings handles errors gracefully."""
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
        
        # Create inventory for second booking
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
        
        # Set both to expired
        past_time = timezone.now() - timedelta(minutes=30)
        booking1.expires_at = past_time
        booking1.save(update_fields=['expires_at'])
        
        booking2.expires_at = past_time
        booking2.save(update_fields=['expires_at'])
        
        # Process expired bookings
        processed_count = Booking.process_expired_bookings()
        
        self.assertEqual(processed_count, 2)
        
        # Verify both were expired
        booking1.refresh_from_db()
        booking2.refresh_from_db()
        self.assertEqual(booking1.status, 'cancelled')
        self.assertEqual(booking2.status, 'cancelled')

    def test_10_expiry_field_not_exposed_to_manipulation(self):
        """Test that expiry field cannot be manipulated through API."""
        # Login as user
        self.client.login(email='security@example.com', password='SecurePassword123!')
        
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
        
        # Try to update expiry through API (should not be allowed)
        data = {
            'expires_at': '2099-12-31T23:59:59Z'
        }
        
        response = self.client.put(f'/api/v1/bookings/{booking.id}/', data, content_type='application/json')
        # Should return 405 Method Not Allowed or 403/400
        self.assertIn(response.status_code, [405, 403, 400])

    def test_11_concurrent_expiry_safety(self):
        """Test that concurrent expiry operations are safe through status validation."""
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
        
        # First expiry should succeed
        booking.expire_booking()
        self.assertEqual(booking.status, 'cancelled')
        
        # Second expiry attempt should fail due to status validation
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as context:
            booking.expire_booking()
        
        self.assertIn('status', context.exception.message_dict)
        
        # Verify booking remains cancelled
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')

    def test_12_management_command_authentication(self):
        """Test that management command requires proper setup."""
        from django.core.management import call_command
        from io import StringIO
        
        # Create expired booking
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        past_time = timezone.now() - timedelta(minutes=30)
        booking.expires_at = past_time
        booking.save(update_fields=['expires_at'])
        
        # Run command in dry-run mode (should work without auth as it's a management command)
        out = StringIO()
        call_command('process_expired_bookings', '--dry-run', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Dry run mode', output)

    def test_13_inventory_restoration_for_multiple_nights(self):
        """Test that expiry restores inventory for multiple nights accurately."""
        # Create booking for 3 nights
        check_in = date.today() + timedelta(days=30)
        check_out = date.today() + timedelta(days=33)
        
        current_date = check_in
        while current_date < check_out:
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
        
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=check_in,
            check_out=check_out,
            guest_count=2
        )
        
        # Verify inventory was booked for 3 nights
        inventory_records = DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=check_in,
            date__lt=check_out
        )
        self.assertEqual(inventory_records.count(), 3)
        
        for inventory in inventory_records:
            self.assertEqual(inventory.booked_rooms, 1)
        
        # Expire the booking
        booking.expire_booking()
        
        # Verify inventory was restored for all 3 nights
        for inventory in inventory_records:
            inventory.refresh_from_db()
            self.assertEqual(inventory.booked_rooms, 0)

    def test_14_expiry_time_reasonable_default(self):
        """Test that expiry time uses reasonable default (15 minutes)."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        # Check that expiry is reasonable (not too short, not too long)
        time_until_expiry = (booking.expires_at - booking.created_at).total_seconds()
        self.assertGreater(time_until_expiry, 60)  # At least 1 minute
        self.assertLess(time_until_expiry, 3600)  # Less than 1 hour
        self.assertAlmostEqual(time_until_expiry, 900, delta=5)  # Approximately 15 minutes

    def test_15_booking_status_integrity_after_expiry(self):
        """Test that booking status and related fields maintain integrity after expiry."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )
        
        original_payment_status = booking.payment_status
        
        booking.expire_booking()
        
        # Check status integrity
        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(booking.payment_status, original_payment_status)  # Payment status unchanged
        self.assertIsNotNone(booking.cancelled_at)
        self.assertIsNotNone(booking.cancellation_reason)
        self.assertEqual(booking.guest, self.user)
        self.assertEqual(booking.property, self.property)


def run_security_checks():
    """Run all security checks and report results."""
    from django.test.runner import DiscoverRunner
    
    runner = DiscoverRunner(verbosity=2)
    test_suite = runner.test_loader.loadTestsFromTestCase(BookingExpirySecurityCheck)
    result = runner.run_suite(test_suite)
    
    print("\n" + "="*70)
    print("SECURITY REVIEW SUMMARY")
    print("="*70)
    print(f"Total tests: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    if result.wasSuccessful():
        print("✓ ALL SECURITY CHECKS PASSED")
        return 0
    else:
        print("✗ SECURITY CHECKS FAILED")
        return 1


if __name__ == '__main__':
    exit_code = run_security_checks()
    sys.exit(exit_code)
