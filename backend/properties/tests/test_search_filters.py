"""
Search filters that the results page sidebar uses (Phase 2 item 2):
features (has_wifi, ...), min_rating, real date availability, sorting by
rating and review count, and GET /properties/filter-options/.
"""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Review
from properties.models import (
    Amenity, AmenityCategory, DateInventory, Property, PropertyAmenity, PropertyTranslation,
    PropertyType, RatePlan, RoomInventory, RoomType,
)
from users.models import User

SEARCH_URL = '/api/v1/properties/search/'
OPTIONS_URL = '/api/v1/properties/filter-options/'


class SearchFiltersBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(email='owner@example.com', password='x')
        self.hotel = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.hostel = PropertyType.objects.create(name='Hostel', slug='hostel')
        self.unused_type = PropertyType.objects.create(name='Villa', slug='villa')
        self.reviewer_count = 0

    def make_property(self, name, property_type=None, price='60.00', **features):
        prop = Property.objects.create(
            owner=self.owner, property_type=property_type or self.hotel, status='active',
            max_guests=2, bedrooms=1, bathrooms=1, address_line1='1 Main St', city='Tashkent',
            country='Uzbekistan', base_price=Decimal(price), currency='USD', **features,
        )
        PropertyTranslation.objects.create(property=prop, language='en', name=name, description='x')
        return prop

    def review(self, prop, rating, status='approved'):
        self.reviewer_count += 1
        user = User.objects.create_user(email=f'guest{self.reviewer_count}@example.com', password='x')
        Review.objects.create(user=user, property=prop, overall_rating=rating, status=status)

    def open_nights(self, prop, start, nights, rooms=1, closed=(), booked=()):
        room_type = RoomType.objects.create(
            property=prop, name='Double', slug='double', base_price=Decimal('60.00'), total_rooms=rooms,
        )
        rate_plan = RatePlan.objects.create(
            room_type=room_type, name='Standard', slug='standard', base_price=Decimal('60.00'),
        )
        for offset in range(nights):
            day = start + timedelta(days=offset)
            # DateInventory still gates the rate plan's own open/closed flag and rules.
            DateInventory.objects.create(
                rate_plan=rate_plan, date=day, available_rooms=rooms,
                booked_rooms=rooms if day in booked else 0, is_available=day not in closed,
            )
            # RoomInventory (audit #31) is the room type's real, shared room count since
            # 3.3 -- what actually decides whether a room is sold out.
            RoomInventory.objects.create(
                room_type=room_type, date=day, available_rooms=rooms,
                booked_rooms=rooms if day in booked else 0,
            )
        return rate_plan

    def search(self, **params):
        response = self.client.get(SEARCH_URL, params)
        assert response.status_code == 200, response.content
        return response

    def ids(self, response):
        return [result['id'] for result in response.data['results']]


class TestFeaturesFilter(SearchFiltersBase):
    def test_features_keep_only_properties_that_have_all_of_them(self):
        both = self.make_property('Both', has_wifi=True, has_parking=True)
        wifi_only = self.make_property('Wifi', has_wifi=True)
        self.make_property('None')

        assert sorted(self.ids(self.search(features='wifi'))) == sorted([both.id, wifi_only.id])
        assert self.ids(self.search(features='wifi,parking')) == [both.id]

    def test_every_feature_name_maps_to_its_flag(self):
        for feature, flag in [('wifi', 'has_wifi'), ('parking', 'has_parking'), ('ac', 'has_ac'),
                              ('heating', 'has_heating'), ('elevator', 'has_elevator')]:
            prop = self.make_property(feature, **{flag: True})
            assert self.ids(self.search(features=feature)) == [prop.id], feature
            prop.delete()

    def test_unknown_feature_is_a_400(self):
        response = self.client.get(SEARCH_URL, {'features': 'wifi,jacuzzi'})
        assert response.status_code == 400
        assert 'features' in response.data['details']


class TestAmenityAndTypeFilters(SearchFiltersBase):
    def test_property_type_id_filters(self):
        hotel = self.make_property('Hotel')
        hostel = self.make_property('Hostel', property_type=self.hostel)

        assert self.ids(self.search(property_type=self.hostel.id)) == [hostel.id]
        assert self.ids(self.search(property_type=self.hotel.id)) == [hotel.id]

    def test_amenity_ids_filter(self):
        category = AmenityCategory.objects.create(name='General', slug='general')
        pool = Amenity.objects.create(category=category, name='Pool', slug='pool', is_searchable=True)
        with_pool = self.make_property('Pool')
        self.make_property('No pool')
        PropertyAmenity.objects.create(property=with_pool, amenity=pool)

        assert self.ids(self.search(amenities=str(pool.id))) == [with_pool.id]


class TestRatingFilterAndSorting(SearchFiltersBase):
    def setUp(self):
        super().setUp()
        self.great = self.make_property('Great')      # 5, 5 -> 5.0 (2 reviews)
        self.good = self.make_property('Good')        # 4, 4, 4 -> 4.0 (3 reviews)
        self.poor = self.make_property('Poor')        # 2 -> 2.0 (1 review)
        self.unrated = self.make_property('Unrated')  # no approved reviews
        for rating in (5, 5):
            self.review(self.great, rating)
        for rating in (4, 4, 4):
            self.review(self.good, rating)
        self.review(self.poor, 2)
        # Pending and rejected reviews do not count
        self.review(self.unrated, 5, status='pending')
        self.review(self.poor, 5, status='rejected')

    def test_min_rating_keeps_properties_rated_at_least_that(self):
        assert sorted(self.ids(self.search(min_rating=4))) == sorted([self.great.id, self.good.id])
        assert self.ids(self.search(min_rating='4.5')) == [self.great.id]

    def test_min_rating_out_of_range_is_a_400(self):
        assert self.client.get(SEARCH_URL, {'min_rating': 6}).status_code == 400
        assert self.client.get(SEARCH_URL, {'min_rating': 0}).status_code == 400

    def test_sort_by_rating_highest_first_unrated_last(self):
        assert self.ids(self.search(sort='rating')) == [
            self.great.id, self.good.id, self.poor.id, self.unrated.id,
        ]

    def test_sort_by_review_count(self):
        assert self.ids(self.search(sort='reviews')) == [
            self.good.id, self.great.id, self.poor.id, self.unrated.id,
        ]

    def test_results_carry_average_rating_and_review_count(self):
        results = {r['id']: r for r in self.search().data['results']}
        assert results[self.great.id]['average_rating'] == 5.0
        assert results[self.great.id]['review_count'] == 2
        assert results[self.poor.id]['average_rating'] == 2.0
        assert results[self.poor.id]['review_count'] == 1
        assert results[self.unrated.id]['average_rating'] is None
        assert results[self.unrated.id]['review_count'] == 0

    def test_rating_filter_combines_with_amenity_join(self):
        category = AmenityCategory.objects.create(name='General', slug='general')
        pool = Amenity.objects.create(category=category, name='Pool', slug='pool', is_searchable=True)
        PropertyAmenity.objects.create(property=self.great, amenity=pool)
        PropertyAmenity.objects.create(property=self.poor, amenity=pool)

        response = self.search(amenities=str(pool.id), min_rating=3)
        assert self.ids(response) == [self.great.id]
        assert response.data['results'][0]['review_count'] == 2


class TestPriceSorting(SearchFiltersBase):
    def test_price_sorts(self):
        cheap = self.make_property('Cheap', price='30.00')
        pricey = self.make_property('Pricey', price='90.00')
        mid = self.make_property('Mid', price='60.00')

        assert self.ids(self.search(sort='price_asc')) == [cheap.id, mid.id, pricey.id]
        assert self.ids(self.search(sort='price_desc')) == [pricey.id, mid.id, cheap.id]


class TestDateAvailabilityFilter(SearchFiltersBase):
    def setUp(self):
        super().setUp()
        self.check_in = timezone.localdate() + timedelta(days=10)
        self.check_out = self.check_in + timedelta(days=2)

    def search_dates(self):
        return self.ids(self.search(check_in=str(self.check_in), check_out=str(self.check_out)))

    def test_property_with_every_night_open_is_found(self):
        prop = self.make_property('Open')
        self.open_nights(prop, self.check_in, 2)
        assert self.search_dates() == [prop.id]

    def test_property_without_inventory_is_not_found(self):
        self.make_property('No inventory')
        assert self.search_dates() == []

    def test_one_missing_night_hides_the_property(self):
        prop = self.make_property('Half')
        self.open_nights(prop, self.check_in, 1)
        assert self.search_dates() == []

    def test_closed_night_hides_the_property(self):
        prop = self.make_property('Closed')
        self.open_nights(prop, self.check_in, 2, closed={self.check_in + timedelta(days=1)})
        assert self.search_dates() == []

    def test_sold_out_night_hides_the_property(self):
        prop = self.make_property('Sold out')
        self.open_nights(prop, self.check_in, 2, booked={self.check_in})
        assert self.search_dates() == []

    def test_check_out_night_itself_does_not_need_to_be_open(self):
        prop = self.make_property('Checkout closed')
        self.open_nights(prop, self.check_in, 3, closed={self.check_out})
        assert self.search_dates() == [prop.id]

    def test_inactive_rate_plan_does_not_count(self):
        prop = self.make_property('Inactive plan')
        rate_plan = self.open_nights(prop, self.check_in, 2)
        rate_plan.is_active = False
        rate_plan.save()
        assert self.search_dates() == []

    def test_rate_plan_min_nights_longer_than_stay_does_not_count(self):
        prop = self.make_property('Long stays only')
        rate_plan = self.open_nights(prop, self.check_in, 2)
        rate_plan.min_nights = 3
        rate_plan.save()
        assert self.search_dates() == []

    def test_open_nights_on_two_different_rate_plans_do_not_combine(self):
        prop = self.make_property('Split')
        first = self.open_nights(prop, self.check_in, 1)
        second_plan = RatePlan.objects.create(
            room_type=first.room_type, name='Flex', slug='flex', base_price=Decimal('70.00'),
        )
        DateInventory.objects.create(
            rate_plan=second_plan, date=self.check_in + timedelta(days=1), available_rooms=1,
        )
        assert self.search_dates() == []


class TestFilterOptions(SearchFiltersBase):
    def setUp(self):
        super().setUp()
        self.make_property('A', price='40.00', has_wifi=True)
        self.make_property('B', price='120.00', has_wifi=True, has_parking=True)
        self.make_property('C', property_type=self.hostel, price='15.00')
        # Not searchable: does not count anywhere
        draft = self.make_property('Draft', price='999.00', has_wifi=True)
        draft.status = 'draft'
        draft.save()
        category = AmenityCategory.objects.create(name='General', slug='general')
        Amenity.objects.create(category=category, name='Pool', slug='pool', is_searchable=True)
        Amenity.objects.create(category=category, name='Hidden', slug='hidden', is_searchable=False)

    def test_is_public(self):
        assert self.client.get(OPTIONS_URL).status_code == 200

    def test_property_types_come_from_the_database_with_counts(self):
        types = self.client.get(OPTIONS_URL).data['property_types']
        assert types == [
            {'id': self.hostel.id, 'name': 'Hostel', 'slug': 'hostel', 'count': 1},
            {'id': self.hotel.id, 'name': 'Hotel', 'slug': 'hotel', 'count': 2},
        ]

    def test_features_with_counts(self):
        features = {f['id']: f for f in self.client.get(OPTIONS_URL).data['features']}
        assert list(features) == ['wifi', 'parking', 'ac', 'heating', 'elevator']
        assert features['wifi']['count'] == 2
        assert features['parking']['count'] == 1
        assert features['ac']['count'] == 0
        assert features['wifi']['label'] == 'WiFi'

    def test_only_searchable_amenities(self):
        amenities = self.client.get(OPTIONS_URL).data['amenities']
        assert [a['name'] for a in amenities] == ['Pool']

    def test_price_range_of_searchable_properties(self):
        price = self.client.get(OPTIONS_URL).data['price_range']
        assert price == {'min': 15.0, 'max': 120.0}

    def test_sort_options_match_what_search_accepts(self):
        sort_ids = [s['id'] for s in self.client.get(OPTIONS_URL).data['sort_options']]
        assert sort_ids == ['relevance', 'price_asc', 'price_desc', 'rating', 'reviews']
        for sort in sort_ids:
            assert self.client.get(SEARCH_URL, {'sort': sort}).status_code == 200, sort
