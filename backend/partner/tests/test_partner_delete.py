"""
Mehmanxana iyesiniń DELETE i jazbanı óshirmey jasıradı (soft delete).

Bronlar mehmanxanaǵa, xona túrine hám rate plan ǵa PROTECT penen baylanǵan, sol sebepli bronı bar birin
haqıyqıy óshiriw aldın 500 menen tawsılatuǵın edi; bronsız bolsa mehmanxananıń xonaların hám bahaların mángige óshirer
edi.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from common.dates import business_today
from currency.testing import make_usd_rate
from permissions.models import Role
from properties.models import DateInventory, Property, PropertyType, RatePlan, RoomType

User = get_user_model()
API = '/api/v1/partner'


class PartnerSoftDeleteTests(APITestCase):

    def setUp(self):
        role, _created = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
        self.owner = User.objects.create_user(email='owner@example.com', password='OwnerPass#1234', role=role)
        self.guest = User.objects.create_user(email='guest@example.com', password='GuestPass#1234')
        self.property = Property.objects.create(
            owner=self.owner, property_type=PropertyType.objects.create(name='Hotel', slug='hotel'), status='active',
            max_guests=4, bedrooms=1, bathrooms=1, address_line1='1 Main St', city='Tashkent',
            country='Uzbekistan', base_price=100, currency='USD')
        self.room = RoomType.objects.create(
            property=self.property, name='Standard', slug='standard', base_occupancy=2, max_occupancy=2,
            base_price=100, currency='USD', total_rooms=3)
        self.rate = RatePlan.objects.create(
            room_type=self.room, name='Flexible', slug='flexible', rate_type='standard', base_price=100,
            currency='USD', min_nights=1, is_active=True)
        self.client.force_authenticate(user=self.owner)

    def book(self):
        check_in = business_today() + timedelta(days=5)
        DateInventory.objects.create(
            rate_plan=self.rate, date=check_in, available_rooms=3, price=100, currency='USD', is_available=True)
        make_usd_rate()
        return Booking.create_booking(
            guest=self.guest, property_obj=self.property, room_type=self.room, rate_plan=self.rate,
            check_in=check_in, check_out=check_in + timedelta(days=1), guest_count=1)

    def test_deleting_a_property_hides_it_and_keeps_the_row(self):
        response = self.client.delete(f'{API}/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Property.objects.get(pk=self.property.pk).is_deleted)
        listed = self.client.get(f'{API}/properties/').data
        self.assertEqual(len(listed.get('results', listed)), 0)

    def test_deleting_a_property_with_a_booking_is_not_a_server_error(self):
        booking = self.book()

        response = self.client.delete(f'{API}/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Property.objects.get(pk=self.property.pk).is_deleted)
        self.assertTrue(Booking.objects.filter(pk=booking.pk).exists())

    def test_deleting_a_room_type_with_a_booking_is_not_a_server_error(self):
        booking = self.book()

        response = self.client.delete(f'{API}/rooms/{self.room.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(RoomType.objects.get(pk=self.room.pk).is_deleted)
        self.assertTrue(Booking.objects.filter(pk=booking.pk).exists())

    def test_deleting_a_rate_plan_with_a_booking_is_not_a_server_error(self):
        booking = self.book()

        response = self.client.delete(f'{API}/rates/{self.rate.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(RatePlan.objects.get(pk=self.rate.pk).is_deleted)
        self.assertTrue(Booking.objects.filter(pk=booking.pk).exists())

    def test_a_deleted_room_type_and_rate_plan_leave_the_owner_lists(self):
        self.client.delete(f'{API}/rates/{self.rate.id}/')
        self.client.delete(f'{API}/rooms/{self.room.id}/')

        for path in ('rates', 'rooms'):
            listed = self.client.get(f'{API}/{path}/').data
            self.assertEqual(len(listed.get('results', listed)), 0, path)
