"""
GET /bookings/ (the guest's own bookings) is paginated like the other lists:
{count, next, previous, results}, newest first, filters kept, never another guest's booking.
"""
from datetime import timedelta
from decimal import Decimal

from rest_framework.test import APIClient, APITestCase

from bookings.models import Booking
from bookings.tests import test_views
from common.dates import business_today
from users.models import User

URL = '/api/v1/bookings/'


class GuestBookingPagesTests(APITestCase):
    def setUp(self):
        test_views.BookingViewTests.setUp(self)  # property, room type and rate plan of the booking tests

    def add_bookings(self, count, guest=None, status='confirmed'):
        guest = guest or self.user
        created = []
        for index in range(count):
            check_in = business_today() + timedelta(days=30 + index * 3 + len(Booking.objects.all()) * 100)
            created.append(Booking.objects.create(
                guest=guest, property=self.property, status=status, payment_status='paid',
                check_in=check_in, check_out=check_in + timedelta(days=2), number_of_nights=2, number_of_rooms=1,
                guest_count=1, total_price=Decimal('200.00'), currency='USD', guest_full_name='Test User',
                guest_email=guest.email, expires_at=None,
            ))
        return created

    def get(self, query=''):
        self.client.force_authenticate(user=self.user)
        return self.client.get(f'{URL}{query}')

    def test_a_guest_without_bookings_gets_an_empty_page(self):
        response = self.get()
        assert response.status_code == 200
        assert response.data == {'count': 0, 'next': None, 'previous': None, 'results': []}

    def test_the_first_page_holds_twenty_and_links_to_the_next(self):
        self.add_bookings(23)
        response = self.get()
        assert response.status_code == 200
        assert response.data['count'] == 23
        assert len(response.data['results']) == 20
        assert response.data['previous'] is None
        assert response.data['next'].endswith('?page=2')

    def test_the_second_page_holds_the_rest_without_repeats(self):
        self.add_bookings(23)
        first = [row['id'] for row in self.get().data['results']]
        second = self.get('?page=2')
        assert second.status_code == 200
        ids = [row['id'] for row in second.data['results']]
        assert len(ids) == 3 and second.data['next'] is None
        assert not set(ids) & set(first)
        assert len(set(first + ids)) == 23

    def test_newest_booking_comes_first(self):
        old, new = self.add_bookings(2)
        Booking.objects.filter(pk=old.pk).update(created_at=old.created_at - timedelta(days=5))
        assert [row['id'] for row in self.get().data['results']] == [new.id, old.id]

    def test_a_page_beyond_the_last_is_404(self):
        self.add_bookings(2)
        assert self.get('?page=2').status_code == 404

    def test_the_status_filter_counts_and_pages_only_that_status(self):
        self.add_bookings(22, status='confirmed')
        self.add_bookings(3, status='cancelled')
        response = self.get('?status=cancelled')
        assert response.data['count'] == 3
        assert {row['status'] for row in response.data['results']} == {'cancelled'}
        confirmed = self.get('?status=confirmed')
        assert confirmed.data['count'] == 22 and len(confirmed.data['results']) == 20

    def test_another_guests_bookings_never_show_up(self):
        other = User.objects.create_user(email='other@example.com', password='OtherPassword#123', phone_number='+998901112299')
        self.add_bookings(3, guest=other)
        mine = self.add_bookings(1)
        response = self.get()
        assert response.data['count'] == 1
        assert [row['id'] for row in response.data['results']] == [mine[0].id]

    def test_an_anonymous_request_is_refused(self):
        assert APIClient().get(URL).status_code in (401, 403)
