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
            'guest_count': 1,
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

    def test_cancellation_reason_over_the_limit_is_refused(self):
        booking_id = self._book().data['id']

        response = self.client.post(f'/api/v1/bookings/{booking_id}/cancel/', {'cancellation_reason': 'r' * 1001}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Booking.objects.get(pk=booking_id).status, 'pending')
