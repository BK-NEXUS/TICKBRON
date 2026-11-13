"""
TICKBRON bron view leri hám API endpoint leri ushın testler.
"""
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from users.models import User
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory, RoomInventory
from bookings.models import Booking
from currency.testing import make_usd_rate


class BookingViewTests(APITestCase):
    """Bron view leri ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        make_usd_rate()  # R6: USD mehmanxanasın tek kurs bar bolǵanda bronlap boladı
        self.client = APIClient()

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

    def test_create_booking_authenticated(self):
        """Kirgen paydalanıwshı sıpatında bron jaratıwdı testlew."""
        self.client.force_authenticate(user=self.user)

        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00',
            'special_requests': 'Late check-in requested'
        }

        response = self.client.post('/api/v1/bookings/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('confirmation_code', response.data)
        self.assertEqual(response.data['status'], 'confirmed')  # mehmanxanada naqd: bron API birden tastıyıqlaydı (burın 'pending')
        self.assertEqual(response.data['guest_count'], 2)

    def test_create_booking_unauthenticated(self):
        """Kirmegen paydalanıwshı sıpatında bron jaratıwdı testlew."""
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00'
        }

        response = self.client.post('/api/v1/bookings/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_bookings_authenticated(self):
        """Kirgen paydalanıwshı sıpatında bronlardı dizimlewdi testlew."""
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

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/bookings/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['confirmation_code'], booking.confirmation_code)

    def test_list_bookings_unauthenticated(self):
        """Kirmegen paydalanıwshı sıpatında bronlardı dizimlewdi testlew."""
        response = self.client.get('/api/v1/bookings/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_booking_authenticated(self):
        """Kirgen paydalanıwshı sıpatında belgili bronnı alıwdı testlew."""
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
        """Kirmegen paydalanıwshı sıpatında belgili bronnı alıwdı testlew."""
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
        """Kirgen paydalanıwshı sıpatında bronnan bas tartıwdı testlew."""
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
        """Kirmegen paydalanıwshı sıpatında bronnan bas tartıwdı testlew."""
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
        """Jaramsız sana aralıǵı menen bron jaratıwdı testlew."""
        self.client.force_authenticate(user=self.user)

        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_out.strftime('%Y-%m-%d'),
            'check_out': self.check_in.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00'
        }

        response = self.client.post('/api/v1/bookings/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('check_out', response.data['details'])

    def test_create_booking_insufficient_inventory(self):
        """Inventory jetispegende bron jaratıwdı testlew."""
        # RoomInventory xona sanın sistema basqaratuǵın qatar (audit #31)
        current_date = self.check_in
        while current_date < self.check_out:
            RoomInventory.objects.create(room_type=self.room_type, date=current_date, available_rooms=0)
            current_date += timedelta(days=1)

        self.client.force_authenticate(user=self.user)

        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00'
        }

        response = self.client.post('/api/v1/bookings/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Qátelikte bos orın maǵlıwmatı bar ekenin tekseriw
        self.assertIn('availability', str(response.data).lower())

    def test_filter_bookings_by_status(self):
        """Bronlardı status boyınsha filterlewdi testlew."""
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

        Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=check_in2,
            check_out=check_out2,
            guest_count=2
        )

        # Bir bronnan bas tartıw
        booking1.cancel_booking('Test cancellation')

        self.client.force_authenticate(user=self.user)

        # Status boyınsha filterlew
        response = self.client.get('/api/v1/bookings/?status=cancelled')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['status'], 'cancelled')

    def _create_booking_via_api(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/bookings/', {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Booking.objects.get(id=response.data['id'])

    def test_guest_cannot_patch_or_put_booking(self):
        """Mehmanlar status, tólem statusı yamasa bahanı PUT/PATCH arqalı qayta jaza almaydı."""
        booking = self._create_booking_via_api()
        tampered = {'status': 'confirmed', 'payment_status': 'paid', 'total_price': '0.01'}

        patch_response = self.client.patch(f'/api/v1/bookings/{booking.id}/', tampered, format='json')
        put_response = self.client.put(f'/api/v1/bookings/{booking.id}/', tampered, format='json')

        self.assertEqual(patch_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(put_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')  # mehmanxanada naqd: bron API birden tastıyıqlaydı (burın 'pending')
        self.assertEqual(booking.payment_status, 'pending')
        self.assertEqual(booking.total_price, Decimal('200.00'))

    def test_guest_cannot_delete_booking(self):
        """DELETE ruxsat etilmeydi; bron hám onıń inventory ustawı saqlanıp qaladı."""
        booking = self._create_booking_via_api()

        response = self.client.delete(f'/api/v1/bookings/{booking.id}/')

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Booking.objects.filter(id=booking.id).exists())
        inventory = RoomInventory.objects.get(room_type=self.room_type, date=self.check_in)
        self.assertEqual(inventory.booked_rooms, 1)

    def test_booking_serializer_fields_are_read_only(self):
        """BookingSerializer hár kirisiwdi itibarǵa almaydı, sol sebepli onı bron jazıw ushın paydalanıp bolmaydı."""
        from bookings.serializers import BookingSerializer

        booking = self._create_booking_via_api()
        serializer = BookingSerializer(
            booking,
            data={'status': 'confirmed', 'payment_status': 'paid', 'total_price': '0.01', 'guest': 999},
            partial=True
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data, {})

    def test_create_booking_internal_error_does_not_leak_details(self):
        """Kútilmegen ishki qátelik (mısalı xom DB qátesi) klientke jetpewi kerek (audit #24)."""
        from unittest.mock import patch

        self.client.force_authenticate(user=self.user)
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 2, 'expected_arrival_time': '14:00'
        }

        secret = 'CHECK constraint "chk_secret_internal_detail" violated on table bookings_x7f2'
        with patch('bookings.models.Booking.create_booking', side_effect=Exception(secret)):
            response = self.client.post('/api/v1/bookings/', data, format='json')

        self.assertIn(response.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR))
        self.assertNotIn(secret, str(response.data))

    def test_cancel_booking_internal_error_does_not_leak_details(self):
        """Bronnan bas tartıw waqtındaǵı kútilmegen ishki qátelik klientke jetpewi kerek (audit #24)."""
        from unittest.mock import patch

        booking = self._create_booking_via_api()
        secret = 'psycopg2.errors.CheckViolation: internal constraint xyz failed'

        with patch('bookings.models.Booking.cancel_booking', side_effect=Exception(secret)):
            response = self.client.post(f'/api/v1/bookings/{booking.id}/cancel/', {}, format='json')

        self.assertIn(response.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR))
        self.assertNotIn(secret, str(response.data))
