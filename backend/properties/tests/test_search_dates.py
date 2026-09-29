"""
Property search with a date range (E2E BUG 1: check_in/check_out returned 500).
"""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from properties.models import DateInventory, Property, PropertyTranslation, PropertyType, RatePlan, RoomType
from users.models import User

SEARCH_URL = '/api/v1/properties/search/'


class TestSearchWithDates(TestCase):
    def setUp(self):
        owner = User.objects.create_user(email='owner@example.com', password='x')
        hotel = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.property = Property.objects.create(
            owner=owner, property_type=hotel, status='active', max_guests=2, bedrooms=1, bathrooms=1,
            address_line1='1 Main St', city='Tashkent', country='Uzbekistan',
            base_price=Decimal('60.00'), currency='USD',
        )
        PropertyTranslation.objects.create(property=self.property, language='en', name='Test Hotel', description='x')
        self.client = APIClient()

    def test_search_with_check_in_and_check_out_returns_results(self):
        check_in = timezone.localdate() + timedelta(days=3)
        # Search with dates only returns properties open on every night (Phase 2 item 2)
        room_type = RoomType.objects.create(
            property=self.property, name='Double', slug='double', base_price=Decimal('60.00'),
        )
        rate_plan = RatePlan.objects.create(
            room_type=room_type, name='Standard', slug='standard', base_price=Decimal('60.00'),
        )
        for offset in range(2):
            DateInventory.objects.create(rate_plan=rate_plan, date=check_in + timedelta(days=offset), available_rooms=1)
        response = self.client.get(SEARCH_URL, {
            'destination': 'Tashkent', 'check_in': str(check_in), 'check_out': str(check_in + timedelta(days=2)),
        })

        assert response.status_code == 200, response.content
        assert [result['id'] for result in response.data['results']] == [self.property.id]

    def test_check_out_before_check_in_is_a_400(self):
        check_in = timezone.localdate() + timedelta(days=3)
        response = self.client.get(SEARCH_URL, {
            'destination': 'Tashkent', 'check_in': str(check_in), 'check_out': str(check_in - timedelta(days=1)),
        })

        assert response.status_code == 400

    def test_search_without_dates_still_works(self):
        response = self.client.get(SEARCH_URL, {'destination': 'Tashkent'})

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_search_excludes_a_room_type_actually_sold_out_via_another_rate_plan(self):
        """
        3.4 (audit #31): RoomInventory is the real, shared-per-room-type room count since
        3.3; DateInventory's own available_rooms/booked_rooms columns are stale, the
        booking engine stopped writing them. Search must not show a property bookable
        through a rate plan whose one physical room was actually sold through a
        different rate plan on the same room type.
        """
        from bookings.models import Booking

        check_in = timezone.localdate() + timedelta(days=5)
        check_out = check_in + timedelta(days=1)
        room_type = RoomType.objects.create(
            property=self.property, name='Last Room', slug='last-room',
            base_price=Decimal('60.00'), total_rooms=1,
        )
        rate_plan_a = RatePlan.objects.create(
            room_type=room_type, name='Rate A', slug='rate-a', base_price=Decimal('60.00'), min_nights=1,
        )
        rate_plan_b = RatePlan.objects.create(
            room_type=room_type, name='Rate B', slug='rate-b', base_price=Decimal('60.00'), min_nights=1,
        )
        for rate_plan in (rate_plan_a, rate_plan_b):
            DateInventory.objects.create(
                rate_plan=rate_plan, date=check_in, available_rooms=1, booked_rooms=0, is_available=True,
            )
        guest = User.objects.create_user(email='guest-search@example.com', password='x')
        Booking.create_booking(
            guest=guest, property_obj=self.property, room_type=room_type, rate_plan=rate_plan_a,
            check_in=check_in, check_out=check_out, guest_count=1,
        )

        response = self.client.get(SEARCH_URL, {
            'destination': 'Tashkent', 'check_in': str(check_in), 'check_out': str(check_out),
        })

        assert response.status_code == 200, response.content
        assert self.property.id not in [result['id'] for result in response.data['results']]
