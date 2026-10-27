"""
One account cannot hold a hotel's rooms (owner decision 2026-10-23): at most two upcoming bookings at once,
and a new stay must not overlap another stay of the same guest. A second booking is fine when its dates start
the day the first one ends or later (or end before the first starts).
"""
from datetime import timedelta

from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from bookings.tests import test_views
from bookings.tests.stays import stay
from common.dates import business_today
from users.models import User


class GuestBookingRulesTests(APITestCase):
    def setUp(self):
        test_views.BookingViewTests.setUp(self)  # hotel, room type, rate plan, a guest
        self.client.force_authenticate(user=self.user)

    def book(self, dates, guest=None):
        if guest:
            self.client.force_authenticate(user=guest)
        body = {
            'property_id': self.property.id, 'room_type_id': self.room_type.id, 'rate_plan_id': self.rate_plan.id,
            'guest_count': 1, 'expected_arrival_time': '14:00', **dates,
        }
        response = self.client.post('/api/v1/bookings/', body, format='json')
        self.client.force_authenticate(user=self.user)
        return response

    def test_the_limit_is_two_upcoming_bookings(self):
        from bookings.views import MAX_UPCOMING_BOOKINGS_PER_GUEST
        assert MAX_UPCOMING_BOOKINGS_PER_GUEST == 2

    def test_a_second_booking_is_allowed_and_a_third_is_not(self):
        assert self.book(stay(self, 0)).status_code == status.HTTP_201_CREATED
        assert self.book(stay(self, 1)).status_code == status.HTTP_201_CREATED
        response = self.book(stay(self, 2))
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data['code'] == 'too_many_upcoming_bookings'
        assert Booking.objects.filter(guest=self.user).count() == 2

    def test_a_stay_overlapping_an_existing_one_is_refused(self):
        first = stay(self, 0, nights=4)  # days 10 to 14
        assert self.book(first).status_code == status.HTTP_201_CREATED
        for index, nights, first_day in [(0, 2, 10), (0, 2, 12), (0, 2, 11), (0, 6, 9), (0, 1, 13)]:
            response = self.book(stay(self, index, nights=nights, first_day=first_day))
            assert response.status_code == status.HTTP_409_CONFLICT, (nights, first_day, response.data)
            assert response.data['code'] == 'overlapping_booking'
        assert Booking.objects.filter(guest=self.user).count() == 1

    def test_a_stay_that_starts_the_day_the_first_ends_is_allowed(self):
        assert self.book(stay(self, 0, nights=4)).status_code == status.HTTP_201_CREATED  # days 10 to 14
        assert self.book(stay(self, 0, nights=2, first_day=14)).status_code == status.HTTP_201_CREATED

    def test_a_stay_that_ends_the_day_the_first_starts_is_allowed(self):
        assert self.book(stay(self, 0, nights=2, first_day=12)).status_code == status.HTTP_201_CREATED  # days 12 to 14
        assert self.book(stay(self, 0, nights=2, first_day=10)).status_code == status.HTTP_201_CREATED

    def test_a_cancelled_booking_does_not_block_its_dates(self):
        assert self.book(stay(self, 0)).status_code == status.HTTP_201_CREATED
        Booking.objects.get(guest=self.user).cancel_booking('user_cancelled')
        assert self.book(stay(self, 0)).status_code == status.HTTP_201_CREATED

    def test_another_guests_booking_does_not_block_the_dates(self):
        other = User.objects.create_user(email='other@example.com', password='OtherPass#123', phone_number='+998901112299')
        assert self.book(stay(self, 0), guest=other).status_code == status.HTTP_201_CREATED
        assert self.book(stay(self, 0)).status_code == status.HTTP_201_CREATED

    def test_a_stay_that_is_over_does_not_count(self):
        past = business_today() - timedelta(days=20)
        Booking.objects.create(
            guest=self.user, property=self.property, status='completed', payment_status='paid',
            check_in=past, check_out=past + timedelta(days=2), number_of_nights=2, number_of_rooms=1, guest_count=1,
            total_price=100, currency='USD', guest_full_name='Test User', guest_email=self.user.email, expires_at=None,
        )
        assert self.book(stay(self, 0)).status_code == status.HTTP_201_CREATED
        assert self.book(stay(self, 1)).status_code == status.HTTP_201_CREATED
