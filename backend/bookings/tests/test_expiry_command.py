"""
TICKBRON bron múddetin ótkeriw management command ı ushın testler.
"""
from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from users.models import User
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory
from bookings.models import Booking
from io import StringIO
from currency.testing import make_usd_rate


class BookingExpiryCommandTests(TestCase):
    """Bron múddetin ótkeriw management command ı ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        make_usd_rate()  # R6: USD mehmanxanasın tek kurs bar bolǵanda bronlap boladı
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

        # Test sanaları ushın date inventory jaratıw
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

    def test_process_expired_bookings_command(self):
        """Management command múddeti ótken bronlardı islewin testlew."""
        # Bron jaratıw
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Múddetin qolda ótkenge qoyıw
        past_time = timezone.now() - timedelta(minutes=30)
        booking.expires_at = past_time
        booking.save(update_fields=['expires_at'])

        # Command ı isletiw
        out = StringIO()
        call_command('process_expired_bookings', stdout=out)

        # Shıǵıwdı tekseriw
        output = out.getvalue()
        self.assertIn('Found 1 expired booking(s) to process', output)
        self.assertIn('Successfully processed 1/1 expired booking(s)', output)

        # Bronnıń múddeti ótkenin tekseriw
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(booking.cancellation_reason, 'Booking expired - payment not completed within time limit')

    def test_process_expired_bookings_dry_run(self):
        """Management command ın dry-run rejiminde testlew."""
        # Bron jaratıw
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Múddetin qolda ótkenge qoyıw
        past_time = timezone.now() - timedelta(minutes=30)
        booking.expires_at = past_time
        booking.save(update_fields=['expires_at'])

        # Command ı dry-run penen isletiw
        out = StringIO()
        call_command('process_expired_bookings', '--dry-run', stdout=out)

        # Shıǵıwdı tekseriw
        output = out.getvalue()
        self.assertIn('Dry run mode', output)
        self.assertIn(booking.confirmation_code, output)

        # Bronnıń múddeti ótpegenin tekseriw
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'pending')

    def test_process_expired_bookings_no_expired(self):
        """Múddeti ótken bron joq bolǵanda management command ın testlew."""
        # Keleshek múddetli bron jaratıw
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Command ı isletiw
        out = StringIO()
        call_command('process_expired_bookings', stdout=out)

        # Shıǵıwdı tekseriw
        output = out.getvalue()
        self.assertIn('No expired bookings to process', output)

        # Bron ele pending ekenin tekseriw
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'pending')

    def test_process_expired_bookings_verbose(self):
        """Management command ın keńeytilgen shıǵıw menen testlew."""
        # Bron jaratıw
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Múddetin qolda ótkenge qoyıw
        past_time = timezone.now() - timedelta(minutes=30)
        booking.expires_at = past_time
        booking.save(update_fields=['expires_at'])

        # Command ı verbose penen isletiw
        out = StringIO()
        call_command('process_expired_bookings', '--verbose', stdout=out)

        # Shıǵıw tolıq maǵlıwmattı óz ishine alǵanın tekseriw
        output = out.getvalue()
        self.assertIn(booking.confirmation_code, output)
        self.assertIn(str(booking.id), output)

    def test_process_expired_bookings_multiple(self):
        """Múddeti ótken kóp bronlardı islewdi testlew."""
        # Bir neshe bron jaratıw
        booking1 = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Ekinshi bron ushın inventory jaratıw
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

        # Ekewin de múddeti ótken etip qoyıw
        past_time = timezone.now() - timedelta(minutes=30)
        booking1.expires_at = past_time
        booking1.save(update_fields=['expires_at'])

        booking2.expires_at = past_time
        booking2.save(update_fields=['expires_at'])

        # Command ı isletiw
        out = StringIO()
        call_command('process_expired_bookings', stdout=out)

        # Shıǵıwdı tekseriw
        output = out.getvalue()
        self.assertIn('Found 2 expired booking(s) to process', output)
        self.assertIn('Successfully processed 2/2 expired booking(s)', output)

        # Ekewiniń de múddeti ótkenin tekseriw
        booking1.refresh_from_db()
        booking2.refresh_from_db()
        self.assertEqual(booking1.status, 'cancelled')
        self.assertEqual(booking2.status, 'cancelled')
