"""The owner's date list must show the real booked rooms, which the booking engine keeps on the room type's RoomInventory."""
from datetime import timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from common.dates import business_today
from permissions.models import Role
from properties.models import DateInventory, Property, PropertyType, RatePlan, RoomInventory, RoomType
from users.models import User


class DateInventoryBookedRoomsTests(TestCase):
    def setUp(self):
        role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'description': 'Owner', 'is_system_role': True})
        self.owner = User.objects.create_user(email='o@example.com', password='testpassword123', role=role)
        kind = PropertyType.objects.create(name='Hotel', slug='hotel')
        prop = Property.objects.create(
            owner=self.owner, property_type=kind, status='active', max_guests=4, bedrooms=1, bathrooms=1,
            address_line1='1 Main St', city='Tashkent', country='Uzbekistan', base_price=100, currency='UZS')
        room = RoomType.objects.create(
            property=prop, name='Std', slug='std', base_occupancy=2, max_occupancy=3, base_price=100,
            currency='UZS', total_rooms=5)
        self.rate = RatePlan.objects.create(room_type=room, name='Std', slug='std', base_price=100, currency='UZS')
        self.day = business_today() + timedelta(days=3)
        self.other_day = self.day + timedelta(days=1)
        for day in (self.day, self.other_day):
            DateInventory.objects.create(rate_plan=self.rate, date=day, available_rooms=5, price=100, currency='UZS')
        RoomInventory.objects.create(room_type=room, date=self.day, available_rooms=5, booked_rooms=2)
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def _rows(self):
        data = self.client.get(f'/api/v1/partner/inventory/?rate_plan={self.rate.id}').data
        return {row['date']: row for row in data['results']}

    def test_list_shows_rooms_booked_on_the_room_type(self):
        row = self._rows()[str(self.day)]
        self.assertEqual((row['booked_rooms'], row['remaining_rooms']), (2, 3))

    def test_night_without_room_inventory_shows_nothing_booked(self):
        row = self._rows()[str(self.other_day)]
        self.assertEqual((row['booked_rooms'], row['remaining_rooms']), (0, 5))

    def test_detail_shows_the_same_numbers(self):
        pk = DateInventory.objects.get(rate_plan=self.rate, date=self.day).pk
        data = self.client.get(f'/api/v1/partner/inventory/{pk}/').data
        self.assertEqual((data['booked_rooms'], data['remaining_rooms']), (2, 3))
