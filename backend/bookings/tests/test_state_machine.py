"""
Tests for booking and payment state machine.
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from users.models import User
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory
from bookings.models import Booking, BookingItem
from bookings.state_machine import (
    BookingStateMachine, 
    PaymentStateMachine, 
    BookingPaymentStateMachine,
    BookingState, 
    PaymentState
)


class BookingStateMachineTests(TestCase):
    """Tests for BookingStateMachine."""
    
    def test_valid_transition_pending_to_confirmed(self):
        """Test valid transition from pending to confirmed."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.PENDING, 
            BookingState.CONFIRMED
        )
        self.assertTrue(is_valid)
    
    def test_valid_transition_pending_to_cancelled(self):
        """Test valid transition from pending to cancelled."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.PENDING, 
            BookingState.CANCELLED
        )
        self.assertTrue(is_valid)
    
    def test_valid_transition_confirmed_to_cancelled(self):
        """Test valid transition from confirmed to cancelled."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.CONFIRMED, 
            BookingState.CANCELLED
        )
        self.assertTrue(is_valid)
    
    def test_valid_transition_confirmed_to_completed(self):
        """Test valid transition from confirmed to completed."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.CONFIRMED, 
            BookingState.COMPLETED
        )
        self.assertTrue(is_valid)
    
    def test_valid_transition_confirmed_to_no_show(self):
        """Test valid transition from confirmed to no_show."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.CONFIRMED, 
            BookingState.NO_SHOW
        )
        self.assertTrue(is_valid)
    
    def test_invalid_transition_confirmed_to_pending(self):
        """Test invalid transition from confirmed to pending."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.CONFIRMED, 
            BookingState.PENDING
        )
        self.assertFalse(is_valid)
    
    def test_invalid_transition_cancelled_to_confirmed(self):
        """Test invalid transition from cancelled to confirmed."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.CANCELLED, 
            BookingState.CONFIRMED
        )
        self.assertFalse(is_valid)
    
    def test_invalid_transition_completed_to_cancelled(self):
        """Test invalid transition from completed to cancelled."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.COMPLETED, 
            BookingState.CANCELLED
        )
        self.assertFalse(is_valid)
    
    def test_self_transition_rejected(self):
        """Test that self-transitions are rejected."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.PENDING, 
            BookingState.PENDING
        )
        self.assertFalse(is_valid)
    
    def test_validate_transition_valid(self):
        """Test validate_transition for valid transition."""
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.PENDING, 
            BookingState.CONFIRMED
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_transition_invalid(self):
        """Test validate_transition for invalid transition."""
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.CONFIRMED, 
            BookingState.PENDING
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_transition_with_reason(self):
        """Test validate_transition with correct reason."""
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.PENDING, 
            BookingState.CONFIRMED,
            reason='payment_completed'
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_transition_with_expiry_reason(self):
        """Test validate_transition with expiry reason for pending->cancelled."""
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.PENDING, 
            BookingState.CANCELLED,
            reason='expiry'
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_transition_with_wrong_reason(self):
        """Test validate_transition with incorrect reason."""
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.PENDING, 
            BookingState.CONFIRMED,
            reason='wrong_reason'
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_get_transition_reason(self):
        """Test getting transition reason."""
        reason = BookingStateMachine.get_transition_reason(
            BookingState.PENDING, 
            BookingState.CONFIRMED
        )
        self.assertEqual(reason, 'payment_completed')
    
    def test_get_valid_transitions(self):
        """Test getting valid transitions from a state."""
        valid_transitions = BookingStateMachine.get_valid_transitions(BookingState.PENDING)
        expected = {BookingState.CONFIRMED, BookingState.CANCELLED}
        self.assertEqual(valid_transitions, expected)


class PaymentStateMachineTests(TestCase):
    """Tests for PaymentStateMachine."""
    
    def test_valid_transition_pending_to_paid(self):
        """Test valid transition from pending to paid."""
        is_valid = PaymentStateMachine.can_transition(
            PaymentState.PENDING, 
            PaymentState.PAID
        )
        self.assertTrue(is_valid)
    
    def test_valid_transition_pending_to_failed(self):
        """Test valid transition from pending to failed."""
        is_valid = PaymentStateMachine.can_transition(
            PaymentState.PENDING, 
            PaymentState.FAILED
        )
        self.assertTrue(is_valid)
    
    def test_valid_transition_paid_to_refunded(self):
        """Test valid transition from paid to refunded."""
        is_valid = PaymentStateMachine.can_transition(
            PaymentState.PAID, 
            PaymentState.REFUNDED
        )
        self.assertTrue(is_valid)
    
    def test_valid_transition_paid_to_partially_refunded(self):
        """Test valid transition from paid to partially_refunded."""
        is_valid = PaymentStateMachine.can_transition(
            PaymentState.PAID, 
            PaymentState.PARTIALLY_REFUNDED
        )
        self.assertTrue(is_valid)
    
    def test_valid_transition_partially_refunded_to_refunded(self):
        """Test valid transition from partially_refunded to refunded."""
        is_valid = PaymentStateMachine.can_transition(
            PaymentState.PARTIALLY_REFUNDED, 
            PaymentState.REFUNDED
        )
        self.assertTrue(is_valid)
    
    def test_invalid_transition_paid_to_pending(self):
        """Test invalid transition from paid to pending."""
        is_valid = PaymentStateMachine.can_transition(
            PaymentState.PAID, 
            PaymentState.PENDING
        )
        self.assertFalse(is_valid)
    
    def test_invalid_transition_failed_to_paid(self):
        """Test invalid transition from failed to paid."""
        is_valid = PaymentStateMachine.can_transition(
            PaymentState.FAILED, 
            PaymentState.PAID
        )
        self.assertFalse(is_valid)
    
    def test_self_transition_rejected(self):
        """Test that self-transitions are rejected."""
        is_valid = PaymentStateMachine.can_transition(
            PaymentState.PENDING, 
            PaymentState.PENDING
        )
        self.assertFalse(is_valid)
    
    def test_validate_transition_valid(self):
        """Test validate_transition for valid transition."""
        is_valid, error = PaymentStateMachine.validate_transition(
            PaymentState.PENDING, 
            PaymentState.PAID
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_transition_invalid(self):
        """Test validate_transition for invalid transition."""
        is_valid, error = PaymentStateMachine.validate_transition(
            PaymentState.PAID, 
            PaymentState.PENDING
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_get_transition_reason(self):
        """Test getting transition reason."""
        reason = PaymentStateMachine.get_transition_reason(
            PaymentState.PENDING, 
            PaymentState.PAID
        )
        self.assertEqual(reason, 'payment_completed')


class BookingPaymentStateMachineTests(TestCase):
    """Tests for BookingPaymentStateMachine."""
    
    def test_valid_combined_transition_pending_to_confirmed_paid(self):
        """Test valid combined transition from pending/pending to confirmed/paid."""
        is_valid = BookingPaymentStateMachine.can_transition_combined(
            BookingState.PENDING, 
            PaymentState.PENDING,
            BookingState.CONFIRMED, 
            PaymentState.PAID
        )
        self.assertTrue(is_valid)
    
    def test_valid_combined_transition_pending_to_cancelled_failed(self):
        """Test valid combined transition from pending/pending to cancelled/failed."""
        is_valid = BookingPaymentStateMachine.can_transition_combined(
            BookingState.PENDING, 
            PaymentState.PENDING,
            BookingState.CANCELLED, 
            PaymentState.FAILED
        )
        self.assertTrue(is_valid)
    
    def test_valid_combined_transition_confirmed_to_cancelled_refunded(self):
        """Test valid combined transition from confirmed/paid to cancelled/refunded."""
        is_valid = BookingPaymentStateMachine.can_transition_combined(
            BookingState.CONFIRMED, 
            PaymentState.PAID,
            BookingState.CANCELLED, 
            PaymentState.REFUNDED
        )
        self.assertTrue(is_valid)
    
    def test_valid_combined_transition_confirmed_to_completed_paid(self):
        """Test valid combined transition from confirmed/paid to completed/paid."""
        is_valid = BookingPaymentStateMachine.can_transition_combined(
            BookingState.CONFIRMED, 
            PaymentState.PAID,
            BookingState.COMPLETED, 
            PaymentState.PAID
        )
        self.assertTrue(is_valid)
    
    def test_invalid_combined_transition_confirmed_to_pending_paid(self):
        """Test invalid combined transition from confirmed/paid to pending/paid."""
        is_valid = BookingPaymentStateMachine.can_transition_combined(
            BookingState.CONFIRMED, 
            PaymentState.PAID,
            BookingState.PENDING, 
            PaymentState.PAID
        )
        self.assertFalse(is_valid)
    
    def test_validate_combined_transition_valid(self):
        """Test validate_transition_combined for valid transition."""
        is_valid, error = BookingPaymentStateMachine.validate_transition_combined(
            BookingState.PENDING, 
            PaymentState.PENDING,
            BookingState.CONFIRMED, 
            PaymentState.PAID
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_combined_transition_invalid(self):
        """Test validate_transition_combined for invalid transition."""
        is_valid, error = BookingPaymentStateMachine.validate_transition_combined(
            BookingState.CONFIRMED, 
            PaymentState.PAID,
            BookingState.PENDING, 
            PaymentState.PAID
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)


class BookingModelStateMachineIntegrationTests(TestCase):
    """Tests for Booking model integration with state machine."""
    
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
            address_line1='123 Test Street',
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
            is_active=True
        )
        
        # Create date inventory
        check_in = timezone.now().date() + timedelta(days=7)
        check_out = check_in + timedelta(days=3)
        
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
        
        # Create booking
        self.booking = Booking.objects.create(
            guest=self.user,
            property=self.property,
            status='pending',
            payment_status='pending',
            check_in=check_in,
            check_out=check_out,
            number_of_nights=3,
            guest_count=2,
            total_price=Decimal('300.00'),
            currency='USD',
            confirmation_code='TEST12345'
        )
        
        BookingItem.objects.create(
            booking=self.booking,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )
    
    def test_confirm_booking_valid_transition(self):
        """Test confirm_booking performs valid state transition."""
        self.booking.confirm_booking()
        self.booking.refresh_from_db()
        
        self.assertEqual(self.booking.status, 'confirmed')
        self.assertEqual(self.booking.payment_status, 'paid')
    
    def test_confirm_booking_invalid_status(self):
        """Test confirm_booking fails for invalid status."""
        self.booking.status = 'cancelled'
        self.booking.save()
        
        with self.assertRaises(Exception):
            self.booking.confirm_booking()
    
    def test_cancel_booking_valid_transition(self):
        """Test cancel_booking performs valid state transition."""
        # First set the booking items to have proper inventory
        from properties.models import DateInventory
        check_in = self.booking.check_in
        check_out = self.booking.check_out
        
        current_date = check_in
        while current_date < check_out:
            DateInventory.objects.filter(
                rate_plan=self.rate_plan,
                date=current_date
            ).update(booked_rooms=1)
            current_date += timedelta(days=1)
        
        self.booking.cancel_booking('Test cancellation')
        self.booking.refresh_from_db()
        
        self.assertEqual(self.booking.status, 'cancelled')
        self.assertEqual(self.booking.cancellation_reason, 'Test cancellation')
    
    def test_cancel_booking_invalid_status(self):
        """Test cancel_booking fails for invalid status."""
        self.booking.status = 'completed'
        self.booking.save()
        
        with self.assertRaises(Exception):
            self.booking.cancel_booking('Test cancellation')
    
    def test_complete_booking_valid_transition(self):
        """Test complete_booking performs valid state transition."""
        self.booking.status = 'confirmed'
        self.booking.payment_status = 'paid'
        self.booking.save()
        
        self.booking.complete_booking()
        self.booking.refresh_from_db()
        
        self.assertEqual(self.booking.status, 'completed')
    
    def test_complete_booking_invalid_status(self):
        """Test complete_booking fails for invalid status."""
        with self.assertRaises(Exception):
            self.booking.complete_booking()
    
    def test_mark_no_show_valid_transition(self):
        """Test mark_no_show performs valid state transition."""
        self.booking.status = 'confirmed'
        self.booking.payment_status = 'paid'
        self.booking.save()
        
        self.booking.mark_no_show()
        self.booking.refresh_from_db()
        
        self.assertEqual(self.booking.status, 'no_show')
    
    def test_mark_no_show_invalid_status(self):
        """Test mark_no_show fails for invalid status."""
        with self.assertRaises(Exception):
            self.booking.mark_no_show()
    
    def test_update_payment_status_valid_transition(self):
        """Test update_payment_status performs valid state transition."""
        self.booking.update_payment_status('paid')
        self.booking.refresh_from_db()
        
        self.assertEqual(self.booking.payment_status, 'paid')
    
    def test_update_payment_status_invalid_transition(self):
        """Test update_payment_status fails for invalid transition."""
        self.booking.payment_status = 'paid'
        self.booking.save()
        
        with self.assertRaises(Exception):
            self.booking.update_payment_status('pending')
    
    def test_booking_clean_validates_state_transition(self):
        """Test booking clean method validates state transitions."""
        # First save the booking with pending status
        self.booking.save()
        
        # Then try to change to an invalid status (cancelled to confirmed is invalid)
        self.booking.status = 'cancelled'
        self.booking.save()
        
        # Now try to change back to confirmed (invalid transition)
        self.booking.status = 'confirmed'
        
        # This should raise validation error since cancelled->confirmed is invalid
        with self.assertRaises(Exception):
            self.booking.full_clean()
    
    def test_expire_booking_valid_transition(self):
        """Test expire_booking performs valid state transition."""
        # First set the booking items to have proper inventory
        from properties.models import DateInventory
        check_in = self.booking.check_in
        check_out = self.booking.check_out
        
        current_date = check_in
        while current_date < check_out:
            DateInventory.objects.filter(
                rate_plan=self.rate_plan,
                date=current_date
            ).update(booked_rooms=1)
            current_date += timedelta(days=1)
        
        self.booking.expire_booking()
        self.booking.refresh_from_db()
        
        self.assertEqual(self.booking.status, 'cancelled')
        self.assertIn('expired', self.booking.cancellation_reason.lower())
    
    def test_expire_booking_invalid_status(self):
        """Test expire_booking fails for invalid status."""
        self.booking.status = 'confirmed'
        self.booking.save()
        
        with self.assertRaises(Exception):
            self.booking.expire_booking()