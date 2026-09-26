"""
Only hotel owners (accounts created by a super-admin) and staff can create or
change properties. A regular registered user gets 403 on every endpoint that
writes a Property or anything under it, and cannot give themselves the
hotel-owner role.
"""
from datetime import date, timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from permissions.models import Role
from properties.models import DateInventory, Property, PropertyType, RatePlan, RoomType
from users.models import User

GIF_1X1 = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


@pytest.fixture
def owner_role(db):
    role, _ = Role.objects.get_or_create(
        name='hotel-owner', defaults={'description': 'Hotel owner role', 'is_system_role': True}
    )
    return role


@pytest.fixture
def owner(owner_role):
    return User.objects.create_user(
        email='owner@example.com', password='OwnerPassword#123', role=owner_role
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(email='guest@example.com', password='GuestPassword#123')


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        email='staff@example.com', password='StaffPassword#123', is_staff=True
    )


@pytest.fixture
def inventory(owner):
    property_type = PropertyType.objects.create(name='Hotel', slug='hotel')
    prop = Property.objects.create(
        owner=owner, property_type=property_type, status='active', max_guests=2,
        bedrooms=1, bathrooms=1, address_line1='1 Amir Temur', city='Tashkent',
        country='Uzbekistan', base_price=60, currency='USD',
    )
    room = RoomType.objects.create(
        property=prop, name='Standard', slug='standard', base_occupancy=2,
        max_occupancy=2, base_price=60, currency='USD', total_rooms=3,
    )
    rate = RatePlan.objects.create(
        room_type=room, name='Standard Rate', slug='standard-rate', rate_type='standard',
        base_price=60, currency='USD', min_nights=1, is_active=True,
    )
    day = DateInventory.objects.create(
        rate_plan=rate, date=date.today(), available_rooms=3, booked_rooms=0,
        price=60, currency='USD', is_available=True,
    )
    return {'property_type': property_type, 'property': prop, 'room': room, 'rate': rate, 'day': day}


def client_for(user):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def create_requests(inv):
    """(url, payload, format) for every partner endpoint that creates something."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    return [
        ('/api/v1/partner/properties/', {
            'property_type': inv['property_type'].id, 'max_guests': 2, 'bedrooms': 1,
            'bathrooms': 1, 'address_line1': '2 Navoi', 'city': 'Tashkent',
            'country': 'Uzbekistan', 'base_price': '70.00', 'currency': 'USD',
        }, 'json'),
        ('/api/v1/partner/rooms/', {
            'property': inv['property'].id, 'name': 'Deluxe', 'slug': 'deluxe',
            'base_occupancy': 2, 'max_occupancy': 3, 'base_price': '90.00',
            'currency': 'USD', 'total_rooms': 2,
        }, 'json'),
        ('/api/v1/partner/rates/', {
            'room_type': inv['room'].id, 'name': 'Flexible', 'slug': 'flexible',
            'rate_type': 'standard', 'base_price': '65.00', 'currency': 'USD',
            'min_nights': 1, 'is_active': True,
        }, 'json'),
        ('/api/v1/partner/inventory/', {
            'rate_plan': inv['rate'].id, 'date': tomorrow, 'available_rooms': 3,
            'price': '60.00', 'currency': 'USD', 'is_available': True,
        }, 'json'),
        (f"/api/v1/partner/properties/{inv['property'].id}/photos/", {
            'photo': SimpleUploadedFile('photo.gif', GIF_1X1, content_type='image/gif'),
            'photo_type': 'exterior',
        }, 'multipart'),
    ]


def update_urls(inv):
    return [
        f"/api/v1/partner/properties/{inv['property'].id}/",
        f"/api/v1/partner/rooms/{inv['room'].id}/",
        f"/api/v1/partner/rates/{inv['rate'].id}/",
        f"/api/v1/partner/inventory/{inv['day'].id}/",
    ]


@pytest.mark.django_db
class TestRegularUserCannotCreateProperties:

    def test_regular_user_gets_403_on_every_create_endpoint(self, regular_user, inventory):
        client = client_for(regular_user)
        counts_before = (Property.objects.count(), RoomType.objects.count(),
                         RatePlan.objects.count(), DateInventory.objects.count())

        for url, payload, fmt in create_requests(inventory):
            response = client.post(url, payload, format=fmt)
            assert response.status_code == 403, url

        assert (Property.objects.count(), RoomType.objects.count(),
                RatePlan.objects.count(), DateInventory.objects.count()) == counts_before

    def test_anonymous_user_is_rejected_on_every_create_endpoint(self, inventory):
        client = client_for(None)
        for url, payload, fmt in create_requests(inventory):
            response = client.post(url, payload, format=fmt)
            assert response.status_code in (401, 403), url
        assert Property.objects.count() == 1

    def test_regular_user_gets_403_on_every_update_and_delete(self, regular_user, inventory):
        client = client_for(regular_user)
        for url in update_urls(inventory):
            assert client.patch(url, {'currency': 'UZS'}, format='json').status_code == 403, url
            assert client.put(url, {}, format='json').status_code == 403, url
            assert client.delete(url).status_code == 403, url
        inventory['property'].refresh_from_db()
        assert inventory['property'].currency == 'USD'
        assert not inventory['property'].is_deleted

    def test_regular_user_cannot_approve_or_suspend_a_property(self, regular_user, inventory):
        client = client_for(regular_user)
        prop_id = inventory['property'].id
        assert client.post(f'/api/v1/admin-panel/properties/{prop_id}/approve/', {}).status_code == 403
        assert client.post(f'/api/v1/admin-panel/properties/{prop_id}/suspend/', {}).status_code == 403
        inventory['property'].refresh_from_db()
        assert inventory['property'].status == 'active'


@pytest.mark.django_db
class TestHotelOwnerAndStaffCanCreate:

    def test_hotel_owner_can_use_every_create_endpoint(self, owner, inventory):
        client = client_for(owner)
        for url, payload, fmt in create_requests(inventory):
            response = client.post(url, payload, format=fmt)
            assert response.status_code == 201, (url, response.data)
        assert Property.objects.filter(owner=owner).count() == 2

    def test_staff_can_create_a_property(self, staff_user, inventory):
        url, payload, fmt = create_requests(inventory)[0]
        response = client_for(staff_user).post(url, payload, format=fmt)
        assert response.status_code == 201
        assert Property.objects.filter(owner=staff_user).count() == 1


@pytest.mark.django_db
class TestRoleCannotBeSelfAssigned:

    def test_register_ignores_role_fields(self, owner_role):
        response = APIClient().post('/api/v1/auth/register/', {
            'email': 'newcomer@example.com', 'full_name': 'New Comer',
            'phone_number': '+998901112233', 'password': 'Str0ng!Passw0rd#',
            'password_confirm': 'Str0ng!Passw0rd#',
            'role': owner_role.id, 'role_name': 'hotel-owner',
            'is_staff': True, 'is_superuser': True,
        }, format='json')

        assert response.status_code == 201, response.data
        user = User.objects.get(email='newcomer@example.com')
        assert user.role is None
        assert user.is_staff is False
        assert user.is_superuser is False
        assert response.data['role'] is None

    def test_profile_update_ignores_role_fields(self, regular_user, owner_role):
        client = client_for(regular_user)
        client.patch('/api/v1/auth/me/update/', {
            'role': owner_role.id, 'role_name': 'hotel-owner', 'is_staff': True,
        }, format='json')

        regular_user.refresh_from_db()
        assert regular_user.role is None
        assert regular_user.is_staff is False
        assert client.post('/api/v1/partner/properties/', {}, format='json').status_code == 403

    def test_otp_login_ignores_role_fields(self, regular_user, owner_role):
        regular_user.phone_number = '+998901234567'
        regular_user.save(update_fields=['phone_number'])
        client = APIClient()
        otp = client.post('/api/v1/auth/otp/request/', {
            'phone_number': regular_user.phone_number, 'role': owner_role.id,
        }, format='json')
        assert otp.status_code == 200
        verify = client.post('/api/v1/auth/otp/verify/', {
            'phone_number': regular_user.phone_number, 'otp_code': otp.data['otp_code'],
            'role': owner_role.id,
        }, format='json')
        assert verify.status_code == 200

        regular_user.refresh_from_db()
        assert regular_user.role is None
        assert verify.data['role'] is None


@pytest.mark.django_db
class TestMeExposesRole:
    """The frontend shows partner entry points only to hotel owners and staff."""

    def test_hotel_owner_sees_their_role(self, owner):
        response = client_for(owner).get('/api/v1/auth/me/')
        assert response.status_code == 200
        assert response.data['role'] == 'hotel-owner'

    def test_regular_user_has_no_role(self, regular_user):
        response = client_for(regular_user).get('/api/v1/auth/me/')
        assert response.data['role'] is None
