"""N-7: one free account must not be able to hold a hotel's inventory."""
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from bookings.tests import test_views
from bookings.tests.stays import stay
from bookings.views import MAX_UPCOMING_BOOKINGS_PER_GUEST  # was MAX_UPCOMING_BOOKINGS_PER_GUEST (unpaid holds)


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
            'expected_arrival_time': '14:00',  # cash at the hotel: the guest names a time
        }
        data.update(extra)
        self.client.force_authenticate(user=self.user)
        return self.client.post('/api/v1/bookings/', data, format='json')

    def test_number_of_rooms_has_an_upper_bound(self):
        response = self._book(number_of_rooms=11)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'number_of_rooms' in response.data['details']

    def test_guest_cannot_hold_more_than_the_upcoming_limit(self):
        for index in range(MAX_UPCOMING_BOOKINGS_PER_GUEST):
            assert self._book(**stay(self, index)).status_code == status.HTTP_201_CREATED

        response = self._book(**stay(self, MAX_UPCOMING_BOOKINGS_PER_GUEST))

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.data['code'] == 'too_many_upcoming_bookings'
        upcoming = Booking.objects.filter(guest=self.user, status='confirmed').count()  # bookings are confirmed at once now
        assert upcoming == MAX_UPCOMING_BOOKINGS_PER_GUEST

    def test_cancelled_booking_frees_a_slot(self):
        for index in range(MAX_UPCOMING_BOOKINGS_PER_GUEST):
            self._book(**stay(self, index))
        # cancel_booking also gives the room back (a plain status update would leave all the rooms taken)
        Booking.objects.filter(guest=self.user).first().cancel_booking('user_cancelled')

        assert self._book(**stay(self, MAX_UPCOMING_BOOKINGS_PER_GUEST)).status_code == status.HTTP_201_CREATED
