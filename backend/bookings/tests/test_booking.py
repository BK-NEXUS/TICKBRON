"""
Transaction qáwipsiz inventory qulıplaw menen TICKBRON bron sisteması ushın testler.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from datetime import date, timedelta
from users.models import User
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory, RoomInventory
from bookings.models import Booking
from bookings.serializers import BookingCreateSerializer, BookingCancelSerializer, BookingSerializer
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError as DRFValidationError


class BookingModelTests(TestCase):
    """Booking modeli ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.user = User.objects.create_user(phone_number='+998901112233',
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

    def test_booking_creation_success(self):
        """Inventory qulıplaw menen tabıslı bron jaratıwdı testlew."""
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

        # Bron elementi jaratılǵanın tekseriw
        self.assertEqual(booking.booking_items.count(), 1)
        booking_item = booking.booking_items.first()
        self.assertEqual(booking_item.room_type, self.room_type)
        self.assertEqual(booking_item.rate_plan, self.rate_plan)
        self.assertEqual(booking_item.number_of_rooms, 1)

        # Inventory jańalanǵanın tekseriw (RoomInventory: usı xona túriniń hár rate
        # plan ı ortaq paydalanadı, qarań bookings.models.Booking.create_booking, audit #31)
        inventory_records = RoomInventory.objects.filter(
            room_type=self.room_type,
            date__gte=self.check_in,
            date__lt=self.check_out
        )
        for inventory in inventory_records:
            self.assertEqual(inventory.booked_rooms, 1)

    def test_booking_creation_insufficient_inventory(self):
        """Inventory jetispegende bron jaratıw sátsiz bolatuǵının testlew."""
        # booked_rooms di available_rooms ǵa teńlew
        current_date = self.check_in
        while current_date < self.check_out:
            RoomInventory.objects.create(
                room_type=self.room_type, date=current_date, available_rooms=5, booked_rooms=5,
            )
            current_date += timedelta(days=1)

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
        """Sana bos bolmaǵanda bron jaratıw sátsiz bolatuǵının testlew."""
        # is_available di False ǵa qoyıw
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
        """Eń kem tún talabı buzılǵanda bron jaratıw sátsiz bolatuǵının testlew."""
        # Rate plan min_nights di jańalaw
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
        """Eń kóp tún talabı buzılǵanda bron jaratıw sátsiz bolatuǵının testlew."""
        # Rate plan max_nights di jańalaw
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
        """Jaramsız sana aralıǵı menen bron jaratıw sátsiz bolatuǵının testlew."""
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
        """Birdey waqıttaǵı sorawlar menen qos bronlawdıń aldı alınatuǵının testlew."""
        # Birinshi bron jaratıw
        Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Jańalanǵan booked_rooms di kóriw ushın inventory di jańalaw (RoomInventory endi
        # xona sanın basqaradı; joqarıdaǵı birinshi bron óz qatarların aldınan jaratqan)
        RoomInventory.objects.filter(
            room_type=self.room_type,
            date__gte=self.check_in,
            date__lt=self.check_out
        ).update(available_rooms=1)  # Jámi tek 1 xona bos

        # Sol sanalar ushın ekinshi bron jaratıp kóriw (sátsiz bolıwı kerek)
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
        """Inventory qaytarıw menen bronnan tabıslı bas tartıwdı testlew."""
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

        # Bronnan bas tartıw
        booking.cancel_booking(cancellation_reason='Test cancellation')

        # Bron statusın tekseriw
        self.assertEqual(booking.status, 'cancelled')
        self.assertIsNotNone(booking.cancelled_at)
        self.assertEqual(booking.cancellation_reason, 'Test cancellation')

        # Inventory qaytarılǵanın tekseriw
        inventory_records = RoomInventory.objects.filter(
            room_type=self.room_type,
            date__gte=self.check_in,
            date__lt=self.check_out
        )
        for inventory in inventory_records:
            self.assertEqual(inventory.booked_rooms, 0)

    def test_booking_cancellation_invalid_status(self):
        """Jaramsız status ushın bronnan bas tartıw sátsiz bolatuǵının testlew."""
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

        # Statusın cancelled etip qoyıw
        booking.status = 'cancelled'
        booking.save()

        # Qayta bas tartıp kóriw (sátsiz bolıwı kerek)
        with self.assertRaises(ValidationError) as context:
            booking.cancel_booking(cancellation_reason='Test cancellation')

        self.assertIn('status', context.exception.message_dict)

    def test_confirmation_code_generation(self):
        """Tastıyıqlaw kodı jaratıw unikal ekenin testlew."""
        booking1 = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Ekinshi bron sanaları ushın inventory jaratıw
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
        self.assertEqual(len(booking1.confirmation_code), 6)  # 23 checkpoint ten beri reference code uzınlıǵı
        self.assertEqual(len(booking2.confirmation_code), 6)


class BookingSerializerTests(TestCase):
    """Bron serializer leri ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.user = User.objects.create_user(phone_number='+998901112233',
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

        # Date inventory jaratıw
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

        # Mock soraw jaratıw
        self.factory = APIRequestFactory()
        self.request = self.factory.post('/api/v1/bookings/')
        self.request.user = self.user

    def test_booking_create_serializer_valid(self):
        """Durıs maǵlıwmat penen bron jaratıw serializer in testlew."""
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00',
            'special_requests': 'Late check-in requested'
        }

        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())

        booking = serializer.save()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.guest, self.user)
        self.assertEqual(booking.status, 'confirmed')  # mehmanxanada naqd: bron API birden tastıyıqlaydı (burın 'pending')

    def test_booking_create_serializer_invalid_date_range(self):
        """Jaramsız sana aralıǵı menen bron jaratıw serializer in testlew."""
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_out.strftime('%Y-%m-%d'),
            'check_out': self.check_in.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00'
        }

        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('check_out', serializer.errors)

    def test_booking_create_serializer_invalid_property(self):
        """Jaramsız mehmanxana menen bron jaratıw serializer in testlew."""
        data = {
            'property_id': 99999,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00'
        }

        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('property_id', serializer.errors)

    def test_booking_create_serializer_exceeds_max_occupancy(self):
        """Mehmanlar sanı eń kóp sıyımlılıqtan asqanda bron jaratıw serializer in testlew."""
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 10, 'expected_arrival_time': '14:00'  # 4 lik max_occupancy dan asadı
        }

        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('guest_count', serializer.errors)

    def test_booking_create_with_guest_details_autofill(self):
        """Bron jaratıw mehman maǵlıwmatın paydalanıwshı profilinen avtomat toltıratuǵının testlew."""
        # Paydalanıwshını profil maǵlıwmatı menen jańalaw
        self.user.full_name = 'John Doe'
        self.user.phone_number = '+998901234567'
        self.user.save()

        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00'
        }

        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())

        booking = serializer.save()
        self.assertEqual(booking.guest_full_name, 'John Doe')
        self.assertEqual(booking.guest_phone, '+998901234567')
        self.assertEqual(booking.guest_email, 'test@example.com')

    def test_booking_create_with_guest_details_override(self):
        """Bron jaratıw mehman maǵlıwmatın almastırıwǵa ruxsat beretuǵının testlew."""
        # Paydalanıwshını profil maǵlıwmatı menen jańalaw
        self.user.full_name = 'John Doe'
        self.user.phone_number = '+998901234567'
        self.user.save()

        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00',
            'guest_full_name': 'Jane Smith',
            'guest_phone': '+998917654321',
            'guest_email': 'jane@example.com'
        }

        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())

        booking = serializer.save()
        self.assertEqual(booking.guest_full_name, 'Jane Smith')
        self.assertEqual(booking.guest_phone, '+998917654321')
        self.assertEqual(booking.guest_email, 'jane@example.com')

    def test_booking_create_with_number_of_rooms(self):
        """Xonalar sanı ózgeshe bolǵanda bron jaratıwdı testlew."""
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00',
            'number_of_rooms': 2
        }

        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())

        booking = serializer.save()
        self.assertEqual(booking.number_of_rooms, 2)
        booking_item = booking.booking_items.first()
        self.assertEqual(booking_item.number_of_rooms, 2)

    def test_booking_create_with_children(self):
        """Balalar jasları menen bron jaratıwdı testlew."""
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 3, 'expected_arrival_time': '14:00',
            'children': [5, 8]
        }

        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())

        booking = serializer.save()
        self.assertEqual(booking.children, [5, 8])

    def _book_with_children(self, guest_count, children, number_of_rooms=1):
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': guest_count, 'expected_arrival_time': '14:00',
            'number_of_rooms': number_of_rooms,
            'children': children,
        }
        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        return serializer.save()

    def test_children_are_part_of_the_guest_count_and_one_adult_is_needed(self):
        for guest_count, children in [(1, [5]), (2, [5, 8]), (3, [1, 2, 3]), (4, [5] * 100)]:
            with self.subTest(guest_count=guest_count, children=len(children)):
                with self.assertRaises(DRFValidationError) as refused:
                    self._book_with_children(guest_count, children)
                self.assertIn('children', refused.exception.detail)
        self.assertEqual(Booking.objects.count(), 0)

    def test_children_up_to_guest_count_minus_one_are_accepted(self):
        booking = self._book_with_children(4, [3, 6, 9])
        self.assertEqual(booking.children, [3, 6, 9])

    def test_no_children_still_works(self):
        self.assertEqual(self._book_with_children(1, []).children, [])

    def test_booking_create_with_invalid_children_age(self):
        """Jaramsız bala jası (teris) menen bron jaratıwdı testlew."""
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00',
            'children': [-1, 5]
        }

        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('children', serializer.errors)

    def test_booking_create_with_invalid_children_age_adult(self):
        """Jaramsız bala jası (úlken adam) menen bron jaratıwdı testlew."""
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00',
            'children': [18, 5]
        }

        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('children', serializer.errors)

    def test_booking_cancel_serializer_valid(self):
        """Durıs maǵlıwmat penen bronnan bas tartıw serializer in testlew."""
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
        """Jaramsız status penen bronnan bas tartıw serializer in testlew."""
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

        # Statusın cancelled etip qoyıw
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

    def test_booking_serializer_includes_new_fields(self):
        """BookingSerializer jańa mehman hám xona maydanların óz ishine alatuǵının testlew."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=3,
            guest_full_name='Test Guest',
            guest_phone='+998901234567',
            guest_email='guest@example.com',
            number_of_rooms=2,
            children=[5, 8]
        )

        serializer = BookingSerializer(booking)
        data = serializer.data

        self.assertIn('guest_full_name', data)
        self.assertIn('guest_phone', data)
        self.assertIn('guest_email', data)
        self.assertIn('number_of_rooms', data)
        self.assertIn('children', data)
        self.assertEqual(data['guest_full_name'], 'Test Guest')
        self.assertEqual(data['guest_phone'], '+998901234567')
        self.assertEqual(data['guest_email'], 'guest@example.com')
        self.assertEqual(data['number_of_rooms'], 2)
        self.assertEqual(data['children'], [5, 8])


class BookingExpiryTests(TestCase):
    """Bron múddeti ótiw funkciyası ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.user = User.objects.create_user(phone_number='+998901112233',
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

    def test_booking_expiry_on_creation(self):
        """Kútip turǵan bronlarǵa múddet waqtı avtomat beriletuǵının testlew."""
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
        # Múddettiń házirgi waqıttan shama menen 15 minut ekenin tekseriw
        from django.utils import timezone
        from datetime import timedelta
        expected_expiry = timezone.now() + timedelta(minutes=15)
        time_difference = abs((booking.expires_at - expected_expiry).total_seconds())
        self.assertLess(time_difference, 5)  # 5 sekund parıqqa ruxsat

    def test_booking_expiry_success(self):
        """Inventory qaytarıw menen bron múddetin tabıslı ótkeriwdi testlew."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Inventory bronlanǵanın tekseriw
        inventory_records = RoomInventory.objects.filter(
            room_type=self.room_type,
            date__gte=self.check_in,
            date__lt=self.check_out
        )
        for inventory in inventory_records:
            self.assertEqual(inventory.booked_rooms, 1)

        # Bronnıń múddetin ótkeriw
        booking.expire_booking()

        # Bron statusın tekseriw
        self.assertEqual(booking.status, 'cancelled')
        self.assertIsNotNone(booking.cancelled_at)
        self.assertEqual(booking.cancellation_reason, 'Booking expired - payment not completed within time limit')

        # Inventory qaytarılǵanın tekseriw
        for inventory in inventory_records:
            inventory.refresh_from_db()
            self.assertEqual(inventory.booked_rooms, 0)

    def test_booking_expiry_invalid_status(self):
        """Kútip turmaǵan status ushın bron múddetin ótkeriw sátsiz bolatuǵının testlew."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Statusın confirmed etip qoyıw
        booking.status = 'confirmed'
        booking.save()

        # Múddetin ótkerip kóriw (sátsiz bolıwı kerek)
        with self.assertRaises(ValidationError) as context:
            booking.expire_booking()

        self.assertIn('status', context.exception.message_dict)

    def test_process_expired_bookings_method(self):
        """Múddeti ótken bronlardı islew klas metodın testlew."""
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

        # Ekinshi bron sanaları ushın inventory jaratıw (qaqtıǵıstan qashıw ushın basqa sanalar)
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

        # Múddet waqıtların qolda ótkenge qoyıw
        from django.utils import timezone
        past_time = timezone.now() - timedelta(minutes=30)

        booking1.expires_at = past_time
        booking1.save(update_fields=['expires_at'])

        booking2.expires_at = past_time
        booking2.save(update_fields=['expires_at'])

        # Múddeti ótken bronlardı islew
        processed_count = Booking.process_expired_bookings()

        self.assertEqual(processed_count, 2)

        # Eki bron da endi biykar etilgenin tekseriw
        booking1.refresh_from_db()
        booking2.refresh_from_db()

        self.assertEqual(booking1.status, 'cancelled')
        self.assertEqual(booking2.status, 'cancelled')
        self.assertEqual(booking1.cancellation_reason, 'Booking expired - payment not completed within time limit')
        self.assertEqual(booking2.cancellation_reason, 'Booking expired - payment not completed within time limit')

    def test_deterministic_state_transitions(self):
        """Bron status ótiwleri anıq hám jaqsı anıqlanǵanın testlew."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Dáslepki jaǵday: pending
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.payment_status, 'pending')

        # 1-ótiw: pending -> cancelled (bas tartıw arqalı)
        booking.cancel_booking('User cancelled')
        self.assertEqual(booking.status, 'cancelled')
        self.assertIsNotNone(booking.cancelled_at)

        # Múddet testi ushın jańa bron jaratıw
        booking2 = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # 2-ótiw: pending -> cancelled (múddet arqalı)
        booking2.expire_booking()
        self.assertEqual(booking2.status, 'cancelled')
        self.assertEqual(booking2.cancellation_reason, 'Booking expired - payment not completed within time limit')

        # Biykar etilgen bronlardan qayta bas tartıp bolmaytuǵının tekseriw
        with self.assertRaises(ValidationError):
            booking.cancel_booking('Try again')

        with self.assertRaises(ValidationError):
            booking2.expire_booking()

    def test_expiry_inventory_restoration_accuracy(self):
        """Múddet ótiw bir neshe xona hám túnler ushın inventory di durıs qaytaratuǵının testlew."""
        # 3 túnlik bron jaratıw (setUp penen qaqtıǵıstan qashıw ushın basqa sanalar)
        check_in = date.today() + timedelta(days=30)
        check_out = date.today() + timedelta(days=33)  # 3 tún

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

        # Inventory 3 túnge bronlanǵanın tekseriw
        inventory_records = RoomInventory.objects.filter(
            room_type=self.room_type,
            date__gte=check_in,
            date__lt=check_out
        )
        self.assertEqual(inventory_records.count(), 3)
        for inventory in inventory_records:
            self.assertEqual(inventory.booked_rooms, 1)

        # Bronnıń múddetin ótkeriw
        booking.expire_booking()

        # Inventory hámme 3 túnge qaytarılǵanın tekseriw
        for inventory in inventory_records:
            inventory.refresh_from_db()
            self.assertEqual(inventory.booked_rooms, 0)


class TransactionSafetyTests(TestCase):
    """Transaction qáwipsizligi hám birdey waqıtlılıq ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.user = User.objects.create_user(phone_number='+998901112233',
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

        # Shekli bos orınlı date inventory jaratıw (bron sisteması haqıyqatında RoomInventory di
        # basqaradı hám jańalaydı -- qarań create_booking, audit #31)
        self.check_in = date.today() + timedelta(days=10)
        self.check_out = date.today() + timedelta(days=12)

        current_date = self.check_in
        while current_date < self.check_out:
            DateInventory.objects.create(
                rate_plan=self.rate_plan,
                date=current_date,
                available_rooms=1,  # Tek 1 xona bos
                booked_rooms=0,
                price=Decimal('100.00'),
                currency='USD',
                is_available=True
            )
            RoomInventory.objects.create(
                room_type=self.room_type, date=current_date, available_rooms=1,  # Tek 1 xona bos
            )
            current_date += timedelta(days=1)

    def test_transaction_rollback_on_error(self):
        """Qátelikte transaction qaytıwın testlew."""
        initial_booked_count = RoomInventory.objects.filter(
            room_type=self.room_type,
            date__gte=self.check_in,
            date__lt=self.check_out
        ).first().booked_rooms

        # Jaramsız maǵlıwmat penen bron jaratıp kóriw (qaytıwı kerek)
        try:
            with transaction.atomic():
                # Bron jaratıw
                Booking.create_booking(
                    guest=self.user,
                    property_obj=self.property,
                    room_type=self.room_type,
                    rate_plan=self.rate_plan,
                    check_in=self.check_in,
                    check_out=self.check_out,
                    guest_count=2
                )

                # Qaytıwdı testlew ushın qátelikti májbúrlew
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Inventory jańalanbaǵanın tekseriw (transaction qaytqan)
        final_booked_count = RoomInventory.objects.filter(
            room_type=self.room_type,
            date__gte=self.check_in,
            date__lt=self.check_out
        ).first().booked_rooms

        self.assertEqual(initial_booked_count, final_booked_count)

    def test_inventory_consistency_after_successful_booking(self):
        """Tabıslı bronnan keyin inventory izbe-iz qalatuǵının testlew."""
        # Inventory dıń dáslepki jaǵdayın alıw
        initial_inventory = list(RoomInventory.objects.filter(
            room_type=self.room_type,
            date__gte=self.check_in,
            date__lt=self.check_out
        ))

        # Bron jaratıw
        Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Inventory izbe-izligin tekseriw
        final_inventory = list(RoomInventory.objects.filter(
            room_type=self.room_type,
            date__gte=self.check_in,
            date__lt=self.check_out
        ))

        for initial, final in zip(initial_inventory, final_inventory):
            self.assertEqual(final.booked_rooms, initial.booked_rooms + 1)
            self.assertEqual(final.available_rooms, initial.available_rooms)
            self.assertEqual(final.remaining_rooms, initial.remaining_rooms - 1)
