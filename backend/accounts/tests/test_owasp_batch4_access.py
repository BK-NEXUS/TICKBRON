"""
A01 (OWASP 2025) access-control details found by the audit:

- favorites exposed hotels that are not published (draft, pending, rejected, suspended)
- the public hotel page returned the owner's and the approving staff member's user ids and the rejection reason
- the public availability returned the partner's internal day notes and had no limit on the date range
- "that booking id does not exist" and "that booking is someone else's" gave different answers
"""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Favorite
from bookings.models import Booking
from common.dates import business_today
from properties.models import DateInventory, Property, PropertyType, RatePlan, RoomType
from properties.tests.test_perf_queries import PropertyFixtureMixin
from users.models import User


class _Fixture(PropertyFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.guest = User.objects.create_user(email='guest@example.com', password='x')
        self.other = User.objects.create_user(email='other@example.com', password='x')
        self.hotel = self.add_hotel(1)
        self.client = APIClient()
        self.client.force_authenticate(self.guest)


class FavoritesOnlyForPublishedHotelsTests(_Fixture):
    def test_a_hotel_that_is_not_published_cannot_be_favorited(self):
        for status in ('pending', 'draft', 'rejected', 'suspended'):
            Property.objects.filter(pk=self.hotel.pk).update(status=status)

            response = self.client.post('/api/v1/me/favorites/', {'property': self.hotel.id}, format='json')

            assert response.status_code == 400, status
        assert not Favorite.objects.filter(user=self.guest).exists()

    def test_a_published_hotel_can_be_favorited(self):
        response = self.client.post('/api/v1/me/favorites/', {'property': self.hotel.id}, format='json')

        assert response.status_code == 201, response.data

    def test_a_favorite_of_a_hotel_that_was_later_suspended_is_not_listed(self):
        Favorite.objects.create(user=self.guest, property=self.hotel)
        Property.objects.filter(pk=self.hotel.pk).update(status='suspended')

        response = self.client.get('/api/v1/me/favorites/')

        rows = response.data['results'] if isinstance(response.data, dict) else response.data
        assert rows == []


class PublicHotelPageHidesInternalFieldsTests(_Fixture):
    def test_detail_has_no_owner_or_moderation_fields(self):
        data = APIClient().get(f'/api/v1/properties/{self.hotel.id}/').data

        for field in ('owner', 'approved_by', 'approved_at', 'rejection_reason'):
            assert field not in data, field

    def test_availability_rows_have_no_internal_notes_and_a_bounded_range(self):
        room = RoomType.objects.get(property=self.hotel)
        plan = RatePlan.objects.get(room_type=room)
        today = business_today()
        for offset, note in ((3, 'Owner lives upstairs'), (700, 'far away')):
            DateInventory.objects.create(
                rate_plan=plan, date=today + timedelta(days=offset), available_rooms=3, booked_rooms=0,
                price=Decimal('40'), currency='USD', is_available=True, notes=note)

        data = APIClient().get(f'/api/v1/properties/{self.hotel.id}/availability/').data

        rows = [row for room_type in data['room_types'] for plan_data in room_type['rate_plans']
                for row in plan_data['date_inventory']]
        assert len(rows) == 1
        assert 'notes' not in rows[0]


class BookingIdGivesNoHintTests(_Fixture):
    def test_review_answers_the_same_for_a_foreign_and_a_missing_booking(self):
        room = RoomType.objects.get(property=self.hotel)
        foreign = Booking.objects.create(
            guest=self.other, property=self.hotel, status='completed', payment_status='paid',
            check_in=business_today() - timedelta(days=5), check_out=business_today() - timedelta(days=3),
            number_of_nights=2, number_of_rooms=1, guest_count=1, total_price=Decimal('80'), currency='USD',
            guest_full_name='Other', guest_email='other@example.com')
        review = {'property': self.hotel.id, 'overall_rating': 5, 'title': 't', 'comment': 'c'}

        for url, body in (('/api/v1/me/reviews/', review),):
            foreign_answer = self.client.post(url, {**body, 'booking': foreign.id}, format='json')
            missing_answer = self.client.post(url, {**body, 'booking': 999999}, format='json')

            assert foreign_answer.status_code == missing_answer.status_code == 400, url
            assert foreign_answer.data == missing_answer.data, url
        assert room
