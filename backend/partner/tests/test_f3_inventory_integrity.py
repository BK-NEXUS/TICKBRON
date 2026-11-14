"""
Security F3: owner inventory endpoints must never let the room counts go wrong (oversell).

DELETE on room-inventory used to remove a night's row, so the next booking re-created it at the full
total_rooms and sold rooms that were already booked or blocked. Prices of 0 or 99999999.99 and a PATCH of
available_rooms under the booked rooms had the same effect on the money and the counts.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from permissions.models import Role
from properties.models import DateInventory, Property, PropertyType, RatePlan, RoomInventory, RoomType
from users.models import User

P = '/api/v1/partner'


@pytest.fixture
def hotel(db):
    role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'description': 'Owner', 'is_system_role': True})
    owner = User.objects.create_user(email='f3owner@example.com', password='OwnerPassword#123', role=role)
    prop = Property.objects.create(
        owner=owner, property_type=PropertyType.objects.create(name='Hotel', slug='hotel-f3'), status='active',
        max_guests=2, bedrooms=1, bathrooms=1, address_line1='1 Main', city='Tashkent', country='Uzbekistan',
        base_price=60, currency='USD',
    )
    room = RoomType.objects.create(
        property=prop, name='Standard', slug='standard-f3', base_occupancy=2, max_occupancy=2,
        base_price=60, currency='USD', total_rooms=5,
    )
    rate = RatePlan.objects.create(
        room_type=room, name='Rate', slug='rate-f3', base_price=Decimal('60.00'), currency='USD',
    )
    day = timezone.localdate() + timedelta(days=5)
    night = RoomInventory.objects.create(room_type=room, date=day, available_rooms=5, booked_rooms=2)
    price_row = DateInventory.objects.create(rate_plan=rate, date=day, available_rooms=5, price=Decimal('60.00'))
    client = APIClient()
    client.force_authenticate(user=owner)
    return {'client': client, 'room': room, 'rate': rate, 'night': night, 'price_row': price_row, 'day': day}


class TestRoomInventoryCannotBeDeleted:
    def test_delete_is_refused_and_the_row_stays(self, hotel):
        response = hotel['client'].delete(f"{P}/room-inventory/{hotel['night'].id}/")
        assert response.status_code == 405
        row = RoomInventory.objects.get(pk=hotel['night'].pk)
        assert not row.is_deleted
        assert row.booked_rooms == 2

    def test_available_rooms_cannot_be_patched_below_the_booked_rooms(self, hotel):
        response = hotel['client'].patch(f"{P}/room-inventory/{hotel['night'].id}/", {'available_rooms': 1})
        assert response.status_code == 400
        assert 'available_rooms' in str(response.data)
        assert RoomInventory.objects.get(pk=hotel['night'].pk).available_rooms == 5

    def test_available_rooms_can_still_be_patched_to_the_booked_rooms(self, hotel):
        response = hotel['client'].patch(f"{P}/room-inventory/{hotel['night'].id}/", {'available_rooms': 2})
        assert response.status_code == 200


class TestNightlyPriceLimits:
    @pytest.mark.parametrize('price', ['0', '0.00', '-1', '99999999.99'])
    def test_inventory_patch_refuses_a_price_outside_the_limits(self, hotel, price):
        response = hotel['client'].patch(f"{P}/inventory/{hotel['price_row'].id}/", {'price': price})
        assert response.status_code == 400
        assert 'price' in str(response.data)
        assert DateInventory.objects.get(pk=hotel['price_row'].pk).price == Decimal('60.00')

    @pytest.mark.parametrize('price', ['0', '99999999.99'])
    def test_bulk_price_refuses_a_price_outside_the_limits(self, hotel, price):
        response = hotel['client'].post(f'{P}/inventory/bulk-price/', {
            'rate_plan': hotel['rate'].id, 'date_from': hotel['day'].isoformat(),
            'date_to': (hotel['day'] + timedelta(days=1)).isoformat(), 'price': price,
        })
        assert response.status_code == 400
        assert DateInventory.objects.get(pk=hotel['price_row'].pk).price == Decimal('60.00')

    def test_an_ordinary_price_is_accepted(self, hotel):
        response = hotel['client'].patch(f"{P}/inventory/{hotel['price_row'].id}/", {'price': '75.00'})
        assert response.status_code == 200

    def test_booked_rooms_cannot_be_written_through_the_inventory_patch(self, hotel):
        response = hotel['client'].patch(f"{P}/inventory/{hotel['price_row'].id}/", {'booked_rooms': 4})
        assert response.status_code == 200
        assert DateInventory.objects.get(pk=hotel['price_row'].pk).booked_rooms == 0
