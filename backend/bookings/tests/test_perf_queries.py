"""R14: the number of queries of the booking lists does not grow with the number of bookings."""
from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from bookings.models import Booking, BookingItem
from bookings.tests import test_views
from common.dates import business_today
from permissions.models import Role


def add_bookings(testcase, count):
    for index in range(count):
        check_in = business_today() + timedelta(days=30 + index * 3)
        booking = Booking.objects.create(
            guest=testcase.user, property=testcase.property, status='confirmed', payment_status='paid',
            check_in=check_in, check_out=check_in + timedelta(days=2), number_of_nights=2, number_of_rooms=1,
            guest_count=1, total_price=Decimal('200.00'), currency='USD', guest_full_name='Test User',
            guest_email=testcase.user.email, expires_at=None,
        )
        BookingItem.objects.create(
            booking=booking, room_type=testcase.room_type, rate_plan=testcase.rate_plan, number_of_rooms=1,
            price_per_night=Decimal('100.00'), currency='USD',
        )


def queries_of(client, url):
    with CaptureQueriesContext(connection) as context:
        response = client.get(url)
    assert response.status_code == 200
    return len(context), response


class GuestBookingListQueryCountTests(APITestCase):
    def setUp(self):
        test_views.BookingViewTests.setUp(self)  # property, room type and rate plan of the booking tests
        self.client.force_authenticate(user=self.user)

    def test_the_list_costs_the_same_for_one_booking_and_for_many(self):
        add_bookings(self, 1)
        few, response = queries_of(self.client, '/api/v1/bookings/')
        assert len(response.data['results']) == 1

        add_bookings(self, 11)
        many, response = queries_of(self.client, '/api/v1/bookings/')
        assert len(response.data['results']) == 12

        assert many == few, f'{few} queries for 1 booking, {many} for 12'

    def test_the_list_stays_within_a_small_budget(self):
        add_bookings(self, 6)

        count, _ = queries_of(self.client, '/api/v1/bookings/')

        assert count <= 8, count


class PartnerBookingListQueryCountTests(APITestCase):
    def setUp(self):
        test_views.BookingViewTests.setUp(self)
        role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'description': 'Hotel owner'})
        self.user.role = role  # the booking tests make this user the property owner
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_the_owner_list_costs_the_same_for_one_booking_and_for_many(self):
        add_bookings(self, 1)
        few, response = queries_of(self.client, '/api/v1/partner/bookings/')
        assert len(response.data) == 1

        add_bookings(self, 11)
        many, response = queries_of(self.client, '/api/v1/partner/bookings/')
        assert len(response.data) == 12

        assert many == few, f'{few} queries for 1 booking, {many} for 12'

    def test_the_owner_list_shows_the_property_name(self):
        add_bookings(self, 1)

        _, response = queries_of(self.client, '/api/v1/partner/bookings/')

        assert response.data[0]['property_name'] == self.property.display_name()
