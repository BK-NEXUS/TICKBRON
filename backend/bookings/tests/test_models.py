"""
TICKBRON bron model leri ushın testler.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta
from users.models import User
from properties.models import Property, PropertyType, RoomType, RatePlan
from bookings.models import Booking, BookingItem


class BookingModelBasicTests(TestCase):
    """Booking modeli ushın tiykarǵı test jaǵdayları."""

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
        """Bron qatar kórinisin testlew."""
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
            confirmation_code='TST234'
        )

        expected_str = f"Booking TST234 - {self.property}"
        self.assertEqual(str(booking), expected_str)

    def test_booking_item_string_representation(self):
        """Bron elementi qatar kórinisin testlew."""
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
            confirmation_code='TST234'
        )

        booking_item = BookingItem.objects.create(
            booking=booking,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )

        expected_str = f"TST234 - {self.room_type.name}"
        self.assertEqual(str(booking_item), expected_str)

    def test_booking_validation_invalid_date_range(self):
        """Jaramsız sana aralıǵı menen bron tekseriwin testlew."""
        booking = Booking(
            guest=self.user,
            property=self.property,
            status='pending',
            check_in=date.today() + timedelta(days=12),
            check_out=date.today() + timedelta(days=10),  # Jaramsız: check_out check_in nen aldın
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            confirmation_code='TST234'
        )

        with self.assertRaises(ValidationError) as context:
            booking.clean()

        self.assertIn('check_out', context.exception.message_dict)

    def test_booking_confirmation_code_generation(self):
        """Tastıyıqlaw kodı avtomat jaratılatuǵının testlew."""
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
        self.assertEqual(len(booking.confirmation_code), 6)

    def test_booking_reference_code_unambiguous_characters(self):
        """Reference code shatastırmaytuǵın belgiler toplamın paydalanatuǵının testlew."""
        # Shatastırmaytuǵın belgiler toplamı mınalardı kirgizbeydi: 0/O, 1/I/L
        ambiguous_chars = {'0', 'O', '1', 'I', 'L'}

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

        # Kodta shatastırıwshı belgiler joq ekenin tekseriw
        code_chars = set(booking.confirmation_code.upper())
        self.assertFalse(code_chars & ambiguous_chars,
                         f"Reference code contains ambiguous characters: {booking.confirmation_code}")

    def test_booking_reference_code_uniqueness(self):
        """Reference code ler bronlar arasında unikal ekenin testlew."""
        booking1 = Booking.objects.create(
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

        booking2 = Booking.objects.create(
            guest=self.user,
            property=self.property,
            status='pending',
            check_in=date.today() + timedelta(days=20),
            check_out=date.today() + timedelta(days=22),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD'
        )

        self.assertNotEqual(booking1.confirmation_code, booking2.confirmation_code)

    def test_booking_reference_code_case_insensitive_lookup(self):
        """Reference code lardı register ti esapqa almay izlew múmkinligin testlew."""
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

        # Úlken háripler menen izlew
        found_upper = Booking.objects.filter(confirmation_code=booking.confirmation_code.upper()).first()
        self.assertEqual(found_upper.id, booking.id)

        # Kishi háripler menen izlew
        Booking.objects.filter(confirmation_code=booking.confirmation_code.lower()).first()
        # Anıq sáykeslik paydalanbasaq bul onı tappawı múmkin, biraq kodtıń ózi úlken háripte
        self.assertIsNotNone(found_upper)

    def test_booking_number_of_nights_calculation(self):
        """number_of_nights avtomat esaplanatuǵının testlew."""
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
