"""
Bron hám tólem state machine ushın testler.
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from users.models import User
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory
from bookings.models import Booking, BookingItem
from bookings.state_machine import BookingStateMachine, BookingState


class BookingStateMachineTests(TestCase):
    """BookingStateMachine ushın testler."""

    def test_valid_transition_pending_to_confirmed(self):
        """pending den confirmed ke jaramlı ótiwdi testlew."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.PENDING,
            BookingState.CONFIRMED
        )
        self.assertTrue(is_valid)

    def test_valid_transition_pending_to_cancelled(self):
        """pending den cancelled ke jaramlı ótiwdi testlew."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.PENDING,
            BookingState.CANCELLED
        )
        self.assertTrue(is_valid)

    def test_valid_transition_confirmed_to_cancelled(self):
        """confirmed den cancelled ke jaramlı ótiwdi testlew."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.CONFIRMED,
            BookingState.CANCELLED
        )
        self.assertTrue(is_valid)

    def test_valid_transition_confirmed_to_completed(self):
        """confirmed den completed ke jaramlı ótiwdi testlew."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.CONFIRMED,
            BookingState.COMPLETED
        )
        self.assertTrue(is_valid)

    def test_valid_transition_confirmed_to_no_show(self):
        """confirmed den no_show ǵa jaramlı ótiwdi testlew."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.CONFIRMED,
            BookingState.NO_SHOW
        )
        self.assertTrue(is_valid)

    def test_invalid_transition_confirmed_to_pending(self):
        """confirmed den pending ke jaramsız ótiwdi testlew."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.CONFIRMED,
            BookingState.PENDING
        )
        self.assertFalse(is_valid)

    def test_invalid_transition_cancelled_to_confirmed(self):
        """cancelled den confirmed ke jaramsız ótiwdi testlew."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.CANCELLED,
            BookingState.CONFIRMED
        )
        self.assertFalse(is_valid)

    def test_invalid_transition_completed_to_cancelled(self):
        """completed den cancelled ke jaramsız ótiwdi testlew."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.COMPLETED,
            BookingState.CANCELLED
        )
        self.assertFalse(is_valid)

    def test_self_transition_rejected(self):
        """Óz-ózine ótiwler biykar etilgenin testlew."""
        is_valid = BookingStateMachine.can_transition(
            BookingState.PENDING,
            BookingState.PENDING
        )
        self.assertFalse(is_valid)

    def test_validate_transition_valid(self):
        """Jaramlı ótiw ushın validate_transition di testlew."""
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.PENDING,
            BookingState.CONFIRMED
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_transition_invalid(self):
        """Jaramsız ótiw ushın validate_transition di testlew."""
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.CONFIRMED,
            BookingState.PENDING
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_transition_with_reason(self):
        """Durıs sebep penen validate_transition di testlew."""
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.PENDING,
            BookingState.CONFIRMED,
            reason='payment_completed'
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_transition_with_expiry_reason(self):
        """pending->cancelled ushın expiry sebebi menen validate_transition di testlew."""
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.PENDING,
            BookingState.CANCELLED,
            reason='expiry'
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_transition_with_wrong_reason(self):
        """Qáte sebep penen validate_transition di testlew."""
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.PENDING,
            BookingState.CONFIRMED,
            reason='wrong_reason'
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_get_transition_reason(self):
        """Ótiw sebebin alıwdı testlew."""
        reason = BookingStateMachine.get_transition_reason(
            BookingState.PENDING,
            BookingState.CONFIRMED
        )
        self.assertEqual(reason, 'payment_completed')

    def test_get_valid_transitions(self):
        """Jaǵdaydan jaramlı ótiwlerdi alıwdı testlew."""
        valid_transitions = BookingStateMachine.get_valid_transitions(BookingState.PENDING)
        expected = {BookingState.CONFIRMED, BookingState.CANCELLED}
        self.assertEqual(valid_transitions, expected)


class BookingModelStateMachineIntegrationTests(TestCase):
    """Booking modeliniń state machine penen integraciyası ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
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

        # Date inventory jaratıw
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

        # Bron jaratıw
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
            confirmation_code='TST345'
        )

        BookingItem.objects.create(
            booking=self.booking,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )

    def test_cancel_booking_valid_transition(self):
        """cancel_booking jaramlı status ótiwin islewin testlew."""
        # Aldın bron elementlerine durıs inventory qoyıw
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
        """cancel_booking jaramsız status ushın sátsiz bolatuǵının testlew."""
        self.booking.status = 'completed'
        self.booking.save()

        with self.assertRaises(Exception):
            self.booking.cancel_booking('Test cancellation')

    def test_complete_booking_valid_transition(self):
        """complete_booking jaramlı status ótiwin islewin testlew."""
        self.booking.status = 'confirmed'
        self.booking.payment_status = 'paid'
        self.booking.save()

        self.booking.complete_booking()
        self.booking.refresh_from_db()

        self.assertEqual(self.booking.status, 'completed')

    def test_complete_booking_invalid_status(self):
        """complete_booking jaramsız status ushın sátsiz bolatuǵının testlew."""
        with self.assertRaises(Exception):
            self.booking.complete_booking()

    def test_mark_no_show_valid_transition(self):
        """mark_no_show jaramlı status ótiwin islewin testlew."""
        self.booking.status = 'confirmed'
        self.booking.payment_status = 'paid'
        self.booking.save()

        self.booking.mark_no_show()
        self.booking.refresh_from_db()

        self.assertEqual(self.booking.status, 'no_show')

    def test_mark_no_show_invalid_status(self):
        """mark_no_show jaramsız status ushın sátsiz bolatuǵının testlew."""
        with self.assertRaises(Exception):
            self.booking.mark_no_show()

    def test_booking_clean_validates_state_transition(self):
        """Booking clean metodı status ótiwlerin tekseretuǵının testlew."""
        # Aldın bronnı pending status penen saqlaw
        self.booking.save()

        # Keyin jaramsız statusqa ózgertip kóriw (cancelled den confirmed ke jaramsız)
        self.booking.status = 'cancelled'
        self.booking.save()

        # Endi qayta confirmed ke ózgertip kóriw (jaramsız ótiw)
        self.booking.status = 'confirmed'

        # Bul validation qátelik kóteriwi kerek, sebebi cancelled->confirmed jaramsız
        with self.assertRaises(Exception):
            self.booking.full_clean()

    def test_expire_booking_valid_transition(self):
        """expire_booking jaramlı status ótiwin islewin testlew."""
        # Aldın bron elementlerine durıs inventory qoyıw
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
        """expire_booking jaramsız status ushın sátsiz bolatuǵının testlew."""
        self.booking.status = 'confirmed'
        self.booking.save()

        with self.assertRaises(Exception):
            self.booking.expire_booking()
