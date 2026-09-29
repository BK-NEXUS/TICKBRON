"""
Access matrix for every /api/v1/partner/ endpoint.

anonymous -> 401/403, regular user -> 403, hotel owner -> only their own data.
"""
from datetime import date, timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from bookings.models import Booking
from permissions.models import Role
from properties.models import DateInventory, Property, PropertyType, RatePlan, RoomBlock, RoomInventory, RoomType
from users.models import User

P = '/api/v1/partner'

# (method, url) for every partner endpoint. Ids do not need to exist:
# permissions are checked before the object is looked up.
PARTNER_ENDPOINTS = [('get', f'{P}/'), ('get', f'{P}/bookings/'), ('post', f'{P}/properties/1/photos/')]
for resource in ('properties', 'rooms', 'rates', 'inventory', 'room-inventory', 'blocks'):
    PARTNER_ENDPOINTS += [
        ('get', f'{P}/{resource}/'),
        ('post', f'{P}/{resource}/'),
        ('get', f'{P}/{resource}/1/'),
        ('put', f'{P}/{resource}/1/'),
        ('patch', f'{P}/{resource}/1/'),
        ('delete', f'{P}/{resource}/1/'),
    ]

GIF_1X1 = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


def call(user, method, url, data=None, fmt='json'):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return getattr(client, method)(url, data or {}, format=fmt)


def results(response):
    data = response.data
    return data['results'] if isinstance(data, dict) and 'results' in data else data


@pytest.fixture
def owner_role(db):
    role, _ = Role.objects.get_or_create(
        name='hotel-owner', defaults={'description': 'Hotel owner role', 'is_system_role': True}
    )
    return role


@pytest.fixture
def guest(db):
    return User.objects.create_user(email='guest@example.com', password='GuestPassword#123')


def make_hotel(owner, city, guest):
    property_type, _ = PropertyType.objects.get_or_create(name='Hotel', slug='hotel')
    prop = Property.objects.create(
        owner=owner, property_type=property_type, status='active', max_guests=2, bedrooms=1,
        bathrooms=1, address_line1='1 Main', city=city, country='Uzbekistan',
        base_price=60, currency='USD',
    )
    room = RoomType.objects.create(
        property=prop, name='Standard', slug='standard', base_occupancy=2, max_occupancy=2,
        base_price=60, currency='USD', total_rooms=3,
    )
    rate = RatePlan.objects.create(
        room_type=room, name='Standard Rate', slug='standard-rate', rate_type='standard',
        base_price=60, currency='USD', min_nights=1, is_active=True,
    )
    check_in = date.today() + timedelta(days=5)
    day = DateInventory.objects.create(
        rate_plan=rate, date=check_in, available_rooms=3, booked_rooms=0,
        price=60, currency='USD', is_available=True,
    )
    room_inventory = RoomInventory.objects.create(
        room_type=room, date=check_in + timedelta(days=10), available_rooms=3, booked_rooms=0,
    )
    block = RoomBlock.create_block(
        room_type=room, date_from=check_in + timedelta(days=20), date_to=check_in + timedelta(days=22),
        rooms=1, note='Booking.com', created_by=owner,
    )
    booking = Booking.create_booking(
        guest=guest, property_obj=prop, room_type=room, rate_plan=rate,
        check_in=check_in, check_out=check_in + timedelta(days=1), guest_count=1,
    )
    return {
        'property': prop, 'room': room, 'rate': rate, 'day': day,
        'room_inventory': room_inventory, 'block': block, 'booking': booking,
    }


@pytest.fixture
def two_owners(owner_role, guest):
    alice = User.objects.create_user(email='alice@example.com', password='AlicePass#1234', role=owner_role)
    bob = User.objects.create_user(email='bob@example.com', password='BobPassword#1234', role=owner_role)
    return {
        'alice': alice, 'bob': bob,
        'alice_hotel': make_hotel(alice, 'Tashkent', guest),
        'bob_hotel': make_hotel(bob, 'Samarkand', guest),
    }


@pytest.mark.django_db
class TestPartnerAccessMatrix:

    @pytest.mark.parametrize('method,url', PARTNER_ENDPOINTS)
    def test_anonymous_is_rejected(self, method, url):
        assert call(None, method, url).status_code in (401, 403)

    @pytest.mark.parametrize('method,url', PARTNER_ENDPOINTS)
    def test_regular_user_gets_403(self, guest, method, url):
        assert call(guest, method, url).status_code == 403


@pytest.mark.django_db
class TestHotelOwnerSeesOnlyOwnData:

    @pytest.mark.parametrize('resource,key', [
        ('properties', 'property'), ('rooms', 'room'), ('rates', 'rate'), ('inventory', 'day'),
        ('room-inventory', 'room_inventory'), ('blocks', 'block'),
    ])
    def test_lists_contain_only_own_objects(self, two_owners, resource, key):
        response = call(two_owners['alice'], 'get', f'{P}/{resource}/')
        assert response.status_code == 200
        if resource == 'room-inventory':
            # the booking in make_hotel() also creates its own RoomInventory row (check_in)
            assert two_owners['alice_hotel'][key].id in [row['id'] for row in results(response)]
            assert two_owners['bob_hotel'][key].id not in [row['id'] for row in results(response)]
        else:
            assert [row['id'] for row in results(response)] == [two_owners['alice_hotel'][key].id]

    @pytest.mark.parametrize('resource,key', [
        ('properties', 'property'), ('rooms', 'room'), ('rates', 'rate'), ('inventory', 'day'),
        ('room-inventory', 'room_inventory'), ('blocks', 'block'),
    ])
    def test_other_owners_objects_are_not_found(self, two_owners, resource, key):
        alice, bob_obj = two_owners['alice'], two_owners['bob_hotel'][key]
        url = f'{P}/{resource}/{bob_obj.id}/'
        assert call(alice, 'get', url).status_code == 404
        if resource != 'blocks':  # blocks has no PATCH/PUT at all (405 regardless of ownership)
            assert call(alice, 'patch', url, {'available_rooms': 1} if resource == 'room-inventory'
                         else {'currency': 'UZS'}).status_code == 404
        assert call(alice, 'delete', url).status_code == 404
        bob_obj.refresh_from_db()
        if resource not in ('room-inventory', 'blocks'):
            assert bob_obj.currency == 'USD'
        assert not bob_obj.is_deleted

    def test_cannot_attach_to_other_owners_objects(self, two_owners):
        alice, bob_hotel = two_owners['alice'], two_owners['bob_hotel']
        room = call(alice, 'post', f'{P}/rooms/', {
            'property': bob_hotel['property'].id, 'name': 'Sneaky', 'slug': 'sneaky',
            'base_occupancy': 1, 'max_occupancy': 1, 'base_price': '1.00', 'currency': 'USD',
            'total_rooms': 1,
        })
        rate = call(alice, 'post', f'{P}/rates/', {
            'room_type': bob_hotel['room'].id, 'name': 'Sneaky', 'slug': 'sneaky',
            'rate_type': 'standard', 'base_price': '1.00', 'currency': 'USD', 'min_nights': 1,
        })
        day = call(alice, 'post', f'{P}/inventory/', {
            'rate_plan': bob_hotel['rate'].id, 'date': (date.today() + timedelta(days=30)).isoformat(),
            'available_rooms': 1, 'price': '1.00', 'currency': 'USD',
        })
        room_inventory = call(alice, 'post', f'{P}/room-inventory/', {
            'room_type': bob_hotel['room'].id, 'date': (date.today() + timedelta(days=30)).isoformat(),
            'available_rooms': 1,
        })
        block = call(alice, 'post', f'{P}/blocks/', {
            'room_type': bob_hotel['room'].id, 'date_from': (date.today() + timedelta(days=40)).isoformat(),
            'date_to': (date.today() + timedelta(days=41)).isoformat(), 'rooms': 1, 'note': 'sneaky',
        })
        photo = call(alice, 'post', f"{P}/properties/{bob_hotel['property'].id}/photos/", {
            'photo': SimpleUploadedFile('p.gif', GIF_1X1, content_type='image/gif'),
            'photo_type': 'exterior',
        }, fmt='multipart')

        assert room.status_code == 400
        assert rate.status_code == 400
        assert day.status_code == 400
        assert room_inventory.status_code == 400
        assert block.status_code == 400
        assert photo.status_code == 404
        assert not RoomType.objects.filter(slug='sneaky').exists()
        assert not RatePlan.objects.filter(slug='sneaky').exists()

    def test_bookings_list_contains_only_own_bookings(self, two_owners):
        response = call(two_owners['alice'], 'get', f'{P}/bookings/')
        assert response.status_code == 200
        assert [row['id'] for row in response.data] == [two_owners['alice_hotel']['booking'].id]
