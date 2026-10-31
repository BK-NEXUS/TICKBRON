"""R14: the number of queries of the search page and the hotel page does not grow with what they show."""
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework import serializers

from properties.models import (
    Amenity, AmenityCategory, Property, PropertyAmenity, PropertyPhoto, PropertyType, RatePlan, RoomType,
)

User = get_user_model()


def queries_of(client, url):
    with CaptureQueriesContext(connection) as context:
        response = client.get(url)
    assert response.status_code == 200, response.content
    return len(context), response


class PropertyFixtureMixin:
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@example.com', password='testpass123')
        self.kind = PropertyType.objects.create(name='Hotel', slug='hotel')
        category = AmenityCategory.objects.create(name='General', slug='general')
        self.amenities = [
            Amenity.objects.create(name=f'Amenity {n}', slug=f'amenity-{n}', category=category, is_searchable=True)
            for n in range(4)
        ]

    def add_hotel(self, number, room_types=1):
        hotel = Property.objects.create(
            owner=self.owner, property_type=self.kind, status='active', is_active=True, max_guests=2, bedrooms=1,
            bathrooms=1, address_line1=f'{number} Test Street', city='Tashkent', country='Uzbekistan',
            base_price=Decimal('40'), currency='USD',
        )
        for index in range(2):
            PropertyPhoto.objects.create(property=hotel, photo=f'p/{number}/{index}.jpg', is_primary=index == 0,
                                         display_order=index)
        for amenity in self.amenities:
            PropertyAmenity.objects.create(property=hotel, amenity=amenity, is_available=True)
        for index in range(room_types):
            room = RoomType.objects.create(
                property=hotel, name=f'Room {index}', slug=f'room-{index}', base_occupancy=2, max_occupancy=2,
                base_price=Decimal('40'), currency='USD', total_rooms=3, bed_configuration='1 Double Bed')
            RatePlan.objects.create(room_type=room, name='Standard', slug='standard', rate_type='standard',
                                    base_price=Decimal('40'), currency='USD', min_nights=1, max_nights=30,
                                    is_active=True)
        return hotel


class SearchQueryCountTests(PropertyFixtureMixin, TestCase):
    URL = '/api/v1/properties/search/'

    def test_the_page_costs_the_same_for_one_hotel_and_for_many(self):
        self.add_hotel(1)
        few, response = queries_of(self.client, self.URL)
        assert len(response.data['results']) == 1

        for number in range(2, 13):
            self.add_hotel(number)
        many, response = queries_of(self.client, self.URL)
        assert len(response.data['results']) == 12

        assert many == few, f'{few} queries for 1 hotel, {many} for 12'

    def test_photo_and_amenities_are_still_returned(self):
        self.add_hotel(1)

        _, response = queries_of(self.client, self.URL)

        row = response.data['results'][0]
        assert row['primary_photo']['is_primary'] is True
        assert len(row['amenities']) == 4


def field_builds_of(client, url):
    """How many times DRF worked out a model serializer's fields (reading the model) while answering the URL."""
    real = serializers.ModelSerializer.get_fields
    with mock.patch.object(serializers.ModelSerializer, 'get_fields', autospec=True, side_effect=real) as spy:
        response = client.get(url)
    assert response.status_code == 200, response.content
    return spy.call_count


class SerializerWorkTests(PropertyFixtureMixin, TestCase):
    """Building a serializer reads the model and is slow: it must not be done once per hotel on a page of hotels."""

    def test_the_search_page_builds_the_same_serializers_for_one_hotel_and_for_many(self):
        self.add_hotel(1)
        few = field_builds_of(self.client, SearchQueryCountTests.URL)
        for number in range(2, 13):
            self.add_hotel(number)

        many = field_builds_of(self.client, SearchQueryCountTests.URL)

        assert many == few, f'{few} serializer builds for 1 hotel, {many} for 12'

    def test_the_hotel_page_builds_the_same_serializers_for_few_and_many_amenities(self):
        hotel = self.add_hotel(1)
        few = field_builds_of(self.client, f'/api/v1/properties/{hotel.id}/')
        category = self.amenities[0].category
        for number in range(10, 20):
            amenity = Amenity.objects.create(name=f'More {number}', slug=f'more-{number}', category=category, is_searchable=True)
            PropertyAmenity.objects.create(property=hotel, amenity=amenity, is_available=True)

        many = field_builds_of(self.client, f'/api/v1/properties/{hotel.id}/')

        assert many == few, f'{few} serializer builds for 4 amenities, {many} for 14'


class DetailQueryCountTests(PropertyFixtureMixin, TestCase):
    def test_the_hotel_page_costs_the_same_for_one_room_type_and_for_many(self):
        hotel = self.add_hotel(1, room_types=1)
        few, _ = queries_of(self.client, f'/api/v1/properties/{hotel.id}/')

        more = self.add_hotel(2, room_types=6)
        many, response = queries_of(self.client, f'/api/v1/properties/{more.id}/')
        assert len(response.data['room_types']) == 6

        assert many == few, f'{few} queries for 1 room type, {many} for 6'


class FavoritesQueryCountTests(PropertyFixtureMixin, TestCase):
    URL = '/api/v1/me/favorites/'

    def favorite(self, hotel):
        from accounts.models import Favorite
        Favorite.objects.create(user=self.guest, property=hotel)

    def setUp(self):
        super().setUp()
        self.guest = User.objects.create_user(email='guest@example.com', password='testpass123')
        self.client.force_login(self.guest)

    def test_the_list_costs_the_same_for_one_favorite_and_for_many(self):
        self.favorite(self.add_hotel(1))
        few, response = queries_of(self.client, self.URL)
        assert len(response.data['results'] if isinstance(response.data, dict) else response.data) == 1

        for number in range(2, 12):
            self.favorite(self.add_hotel(number))
        many, response = queries_of(self.client, self.URL)
        rows = response.data['results'] if isinstance(response.data, dict) else response.data
        assert len(rows) == 11
        assert rows[0]['property_primary_photo']

        assert many == few, f'{few} queries for 1 favorite, {many} for 11'
