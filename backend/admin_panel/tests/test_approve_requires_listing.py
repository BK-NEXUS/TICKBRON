"""
QA finding F3: approving a hotel that has no room, no active rate or no photo made it public with an
empty page. Approval is refused (400, with the list of what is missing) until all three exist.
Rejecting is never blocked.
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from admin_panel.tests.listing_helpers import add_photo, add_rate, add_room, make_listable
from properties.models import Property, PropertyPhoto, PropertyType, RatePlan, RoomType
from users.models import User

A = '/api/v1/admin-panel'


@pytest.fixture
def staff(db):
    return User.objects.create_user(email='staff@example.com', password='x', is_staff=True)


@pytest.fixture
def hotel(db):
    owner = User.objects.create_user(email='owner@example.com', password='x')
    return Property.objects.create(
        owner=owner, property_type=PropertyType.objects.create(name='Hotel', slug='hotel'),
        status='pending_approval', max_guests=2, bedrooms=1, bathrooms=1, city='Tashkent',
        country='Uzbekistan', base_price=Decimal('50'), currency='USD',
    )


def _approve(user, hotel, body=None):
    client = APIClient()
    client.force_authenticate(user=user)
    return client.post(f'{A}/properties/{hotel.id}/approve/', body or {}, format='json')


@pytest.mark.django_db
class TestApproveRequiresListing:
    def test_complete_hotel_is_approved(self, staff, hotel):
        make_listable(hotel)
        assert _approve(staff, hotel).status_code == 200
        hotel.refresh_from_db()
        assert hotel.status == 'active'

    def test_empty_hotel_is_refused_and_lists_everything_missing(self, staff, hotel):
        response = _approve(staff, hotel)
        assert response.status_code == 400
        assert response.data['missing'] == ['room', 'rate', 'photo']
        hotel.refresh_from_db()
        assert hotel.status == 'pending_approval'
        assert hotel.approved_at is None

    def test_missing_photo_only(self, staff, hotel):
        add_rate(add_room(hotel))
        assert _approve(staff, hotel).data['missing'] == ['photo']

    def test_room_withoutadd_rate(self, staff, hotel):
        add_room(hotel)
        add_photo(hotel)
        assert _approve(staff, hotel).data['missing'] == ['rate']

    def test_inactive_rate_does_not_count(self, staff, hotel):
        rate = add_rate(add_room(hotel))
        add_photo(hotel)
        RatePlan.objects.filter(pk=rate.pk).update(is_active=False)
        assert _approve(staff, hotel).data['missing'] == ['rate']

    def test_deleted_room_does_not_count(self, staff, hotel):
        room = add_room(hotel)
        add_rate(room)
        add_photo(hotel)
        RoomType.objects.filter(pk=room.pk).update(is_deleted=True)
        assert _approve(staff, hotel).data['missing'] == ['room', 'rate']

    def test_deleted_rate_does_not_count(self, staff, hotel):
        rate = add_rate(add_room(hotel))
        add_photo(hotel)
        RatePlan.objects.filter(pk=rate.pk).update(is_deleted=True)
        assert _approve(staff, hotel).data['missing'] == ['rate']

    def test_deleted_photo_does_not_count(self, staff, hotel):
        add_rate(add_room(hotel))
        photo = add_photo(hotel)
        PropertyPhoto.objects.filter(pk=photo.pk).update(is_deleted=True)
        assert _approve(staff, hotel).data['missing'] == ['photo']

    def test_rejecting_an_empty_hotel_still_works(self, staff, hotel):
        response = _approve(staff, hotel, {'rejection_reason': 'Add rooms and photos'})
        assert response.status_code == 200
        hotel.refresh_from_db()
        assert hotel.status == 'rejected'

    def test_other_hotels_parts_do_not_count(self, staff, hotel):
        other = Property.objects.create(
            owner=hotel.owner, property_type=hotel.property_type, status='pending_approval',
            max_guests=2, bedrooms=1, bathrooms=1, city='Tashkent', country='Uzbekistan',
            base_price=Decimal('50'), currency='USD',
        )
        make_listable(other)
        assert _approve(staff, hotel).data['missing'] == ['room', 'rate', 'photo']
