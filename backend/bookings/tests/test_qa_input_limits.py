"""QA: free-text booking fields have a length limit (a 200 KB 'special request' was accepted)."""
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from bookings.tests import test_views


class BookingTextLimitTests(APITestCase):
    def setUp(self):
        test_views.BookingViewTests.setUp(self)  # the hotel fixture of the booking view tests
        self.client.force_authenticate(user=self.user)

    def _book(self, **extra):
        data = {
            'property_id': self.property.id, 'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'), 'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 1, 'expected_arrival_time': '14:00',
        }
        data.update(extra)
        return self.client.post('/api/v1/bookings/', data, format='json')

    def test_special_requests_at_the_limit_is_accepted(self):
        response = self._book(special_requests='x' * 1000)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_special_requests_over_the_limit_is_refused(self):
        response = self._book(special_requests='x' * 1001)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('special_requests', response.data['details'])
        self.assertFalse(Booking.objects.exists())

    def test_guest_name_longer_than_the_column_is_refused_not_a_server_error(self):
        response = self._book(guest_full_name='N' * 301)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('guest_full_name', response.data['details'])

    def test_guest_name_with_digits_is_refused(self):
        response = self._book(guest_full_name='Aziz 007')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('guest_full_name', response.data['details'])
        self.assertFalse(Booking.objects.exists())

    def test_cancellation_reason_over_the_limit_is_refused(self):
        booking_id = self._book().data['id']

        response = self.client.post(f'/api/v1/bookings/{booking_id}/cancel/', {'cancellation_reason': 'r' * 1001}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Booking.objects.get(pk=booking_id).status, 'confirmed')  # cash at the hotel: the booking API confirms at once (was 'pending')


class BookingPhoneTests(APITestCase):
    """The guest's phone is required: the booking's own number, else the account's (plan PLAN_CASH_ONLY stage 1)."""

    def setUp(self):
        test_views.BookingViewTests.setUp(self)
        self.client.force_authenticate(user=self.user)

    def _book(self, **extra):
        data = {
            'property_id': self.property.id, 'room_type_id': self.room_type.id, 'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'), 'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 1, 'expected_arrival_time': '14:00', **extra,
        }
        return self.client.post('/api/v1/bookings/', data, format='json')

    def test_no_number_anywhere_is_refused(self):
        self.user.phone_number = None
        self.user.save()
        response = self._book()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('guest_phone', response.data['details'])
        self.assertFalse(Booking.objects.exists())

    def test_the_account_number_is_used_when_the_booking_has_none(self):
        self.user.phone_number = '+998901112233'
        self.user.save()
        response = self._book()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Booking.objects.get().guest_phone, '+998901112233')

    def test_the_booking_number_wins_and_is_stored_in_e164_form(self):
        response = self._book(guest_phone='+998 91 555 44 33')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Booking.objects.get().guest_phone, '+998915554433')

    def test_a_bad_number_is_refused(self):
        response = self._book(guest_phone='12345')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('guest_phone', response.data['details'])

