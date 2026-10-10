"""N-7: one free account must not be able to hold a hotel's inventory."""
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from bookings.tests import test_views
from bookings.views import MAX_PENDING_BOOKINGS_PER_GUEST


class PendingBookingCapTests(APITestCase):
    def setUp(self):
        # Reuse the hotel fixture of the booking view tests without re-running them
        test_views.BookingViewTests.setUp(self)

    def _book(self, **extra):
        data = {
            'property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'),
            'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 1,
        }
        data.update(extra)
        self.client.force_authenticate(user=self.user)
        return self.client.post('/api/v1/bookings/', data, format='json')

    def test_number_of_rooms_has_an_upper_bound(self):
        response = self._book(number_of_rooms=11)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'number_of_rooms' in response.data['details']

    def test_guest_cannot_hold_more_than_the_pending_limit(self):
        for _ in range(MAX_PENDING_BOOKINGS_PER_GUEST):
            assert self._book().status_code == status.HTTP_201_CREATED

        response = self._book()

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.data['code'] == 'too_many_pending_bookings'
        pending = Booking.objects.filter(guest=self.user, status='pending').count()
        assert pending == MAX_PENDING_BOOKINGS_PER_GUEST

    def test_cancelled_booking_frees_a_slot(self):
        for _ in range(MAX_PENDING_BOOKINGS_PER_GUEST):
            self._book()
        Booking.objects.filter(pk=Booking.objects.filter(guest=self.user).first().pk).update(status='cancelled')

        assert self._book().status_code == status.HTTP_201_CREATED
