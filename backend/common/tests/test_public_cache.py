"""
A short copy of the answers that every visitor gets the same (hotel page, availability, search results, filter options):
a few seconds old at most, never for anything that changes with who asks, never for an error, never for the paid banners.
"""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

import pytest
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from common import public_cache
from common.dates import business_today
from promotions.models import PromotionDailyStat
from promotions.tests.helpers import make_hotel, make_owner, make_promotion
from properties.models import PropertyTranslation

pytestmark = pytest.mark.django_db

CACHE_ON = pytest.mark.usefixtures('cache_on')


@pytest.fixture
def cache_on(settings):
    settings.PUBLIC_CACHE_SECONDS = 30


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    public_cache.resume()
    yield
    cache.clear()
    public_cache.resume()


@pytest.fixture
def hotel():
    return make_hotel(make_owner('cache-owner@example.com'), name='Cached Hotel')


def queries_for(url, params=None, **headers):
    with CaptureQueriesContext(connection) as context:
        response = APIClient().get(url, params or {}, **headers)
    return response, len(context)


def detail_url(hotel):
    return f'/api/v1/properties/{hotel.id}/'


def rename(hotel, name):
    PropertyTranslation.objects.filter(property=hotel, language='en').update(name=name)


def name_in(response):
    return next(item['name'] for item in response.data['translations'] if item['language'] == 'en')


class TestSwitch:
    def test_it_is_off_while_the_test_suite_runs_so_other_tests_see_fresh_data(self, hotel):
        assert public_cache.seconds() == 0
        APIClient().get(detail_url(hotel))
        rename(hotel, 'Renamed')

        assert name_in(APIClient().get(detail_url(hotel))) == 'Renamed'

    def test_zero_means_every_answer_is_fresh(self, hotel, settings):
        settings.PUBLIC_CACHE_SECONDS = 0
        APIClient().get(detail_url(hotel))
        rename(hotel, 'Renamed')

        assert name_in(APIClient().get(detail_url(hotel))) == 'Renamed'


@CACHE_ON
class TestHotelPage:
    def test_the_second_visitor_costs_no_database_work(self, hotel):
        first, first_queries = queries_for(detail_url(hotel))
        second, second_queries = queries_for(detail_url(hotel))

        assert first.status_code == second.status_code == 200
        assert first_queries > 0 and second_queries == 0
        assert first.data == second.data

    def test_a_change_shows_after_the_copy_is_dropped(self, hotel):
        APIClient().get(detail_url(hotel))
        rename(hotel, 'Renamed')
        assert name_in(APIClient().get(detail_url(hotel))) == 'Cached Hotel'

        cache.clear()

        assert name_in(APIClient().get(detail_url(hotel))) == 'Renamed'

    def test_a_missing_hotel_is_never_remembered(self, hotel):
        hotel.status = 'pending'
        hotel.save(update_fields=['status'])
        assert APIClient().get(detail_url(hotel)).status_code == 404

        hotel.status = 'active'
        hotel.save(update_fields=['status'])

        assert APIClient().get(detail_url(hotel)).status_code == 200

    def test_each_hotel_has_its_own_copy(self, hotel):
        other = make_hotel(hotel.owner, name='Other Hotel')
        APIClient().get(detail_url(hotel))

        assert name_in(APIClient().get(detail_url(other))) == 'Other Hotel'


@CACHE_ON
class TestSearch:
    URL = '/api/v1/properties/search/'

    def test_the_results_are_copied_per_query_and_page(self, hotel):
        make_hotel(hotel.owner, name='Second Hotel')
        first, first_queries = queries_for(self.URL, {'page_size': 1})
        again, again_queries = queries_for(self.URL, {'page_size': 1})
        other_page, _ = queries_for(self.URL, {'page_size': 1, 'page': 2})

        assert first.data['results'] == again.data['results']
        assert again_queries < first_queries
        assert other_page.data['results'] != first.data['results']

    def test_a_bad_request_is_a_400_every_time_and_is_not_remembered(self):
        for _ in range(2):
            assert APIClient().get(self.URL, {'min_price': '-5'}).status_code == 400

    def test_a_paid_banner_is_counted_for_every_visitor_even_when_the_results_come_from_the_copy(self, hotel):
        promotion = make_promotion(hotel)
        for visitor in range(3):  # a banner is counted once per visitor and hour: three different visitors
            assert APIClient().get(self.URL, REMOTE_ADDR=f'203.0.113.{visitor + 1}').status_code == 200

        stat = PromotionDailyStat.objects.get(promotion=promotion, date=business_today())
        assert stat.impressions == 3


@CACHE_ON
class TestFilterOptionsAndAvailability:
    def test_filter_options_are_copied(self, hotel):
        _, first = queries_for('/api/v1/properties/filter-options/')
        _, second = queries_for('/api/v1/properties/filter-options/')

        assert first > 0 and second == 0

    def test_availability_is_copied_for_the_same_dates_only(self, hotel):
        url = f'/api/v1/properties/{hotel.id}/availability/'
        day = business_today().isoformat()
        _, first = queries_for(url, {'check_in': day})
        _, second = queries_for(url, {'check_in': day})
        _, other_day = queries_for(url, {'check_in': (business_today() + timedelta(days=3)).isoformat()})

        assert second == 0 and first > 0 and other_day > 0

    def test_a_price_quote_is_never_copied_because_it_is_what_a_guest_pays(self, hotel):
        from properties.models import RatePlan, RoomType
        room = RoomType.objects.create(
            property=hotel, name='Room', slug='room', base_occupancy=2, max_occupancy=2, base_price=Decimal('40'),
            currency='UZS', total_rooms=3, bed_configuration='1 Double Bed')
        plan = RatePlan.objects.create(room_type=room, name='Std', slug='std', rate_type='standard', base_price=Decimal('40'),
                                       currency='UZS', min_nights=1, max_nights=30, is_active=True)
        start = business_today() + timedelta(days=5)
        params = {'room_type_id': room.id, 'rate_plan_id': plan.id, 'check_in': start.isoformat(),
                  'check_out': (start + timedelta(days=2)).isoformat()}
        url = f'/api/v1/properties/{hotel.id}/quote/'
        _, first = queries_for(url, params)
        _, second = queries_for(url, params)

        assert second > 0 and first > 0


@CACHE_ON
class TestSuggestionsAndGeography:
    def test_suggestions_are_copied_per_text(self, hotel):
        _, first = queries_for('/api/v1/properties/search/suggestions/', {'q': 'Tash'})
        _, second = queries_for('/api/v1/properties/search/suggestions/', {'q': 'Tash'})
        _, other = queries_for('/api/v1/properties/search/suggestions/', {'q': 'Sam'})

        assert first > 0 and second == 0 and other > 0

    def test_too_short_a_text_is_answered_without_the_database_and_without_a_copy(self):
        response, queries = queries_for('/api/v1/properties/search/suggestions/', {'q': 'T'})

        assert response.data == {'suggestions': []} and queries == 0

    def test_the_country_list_is_copied(self):
        _, first = queries_for('/api/v1/geography/countries/')
        response, second = queries_for('/api/v1/geography/countries/')

        assert response.status_code == 200 and first > 0 and second == 0

    def test_an_unknown_country_is_a_404_every_time(self):
        for _ in range(2):
            assert APIClient().get('/api/v1/geography/countries/XX/regions/').status_code == 404


@CACHE_ON
class TestWhenTheCacheIsDown:
    def test_a_broken_cache_never_breaks_a_page(self, hotel):
        with mock.patch.object(public_cache.cache, 'get', side_effect=ConnectionError('redis is down')), \
                mock.patch.object(public_cache.cache, 'set', side_effect=ConnectionError('redis is down')):
            response = APIClient().get(detail_url(hotel))

        assert response.status_code == 200
        assert name_in(response) == 'Cached Hotel'


@pytest.fixture
def any_host(settings):
    settings.ALLOWED_HOSTS = ['*']


@CACHE_ON
class TestWhenTheCacheStaysDown:
    """Every call to a dead Redis waits for its timeout: after one failure the pages stop asking for a while."""

    def test_after_one_failure_the_cache_is_left_alone_until_the_pause_ends(self, hotel):
        clock = mock.Mock()
        # the time of each look at the clock: is it paused (1st request), start the pause, paused? (2nd), paused? (3rd)
        clock.monotonic.side_effect = [100.0, 100.0, 105.0, 200.0, 200.0]
        with mock.patch.object(public_cache.cache, 'get', side_effect=ConnectionError('redis is down')) as get, \
                mock.patch.object(public_cache.cache, 'set') as put, mock.patch.object(public_cache, 'time', clock):
            APIClient().get(detail_url(hotel))      # fails once and starts the pause
            APIClient().get(detail_url(hotel))      # inside the pause: no call to the cache at all
            assert get.call_count == 1 and put.call_count == 0

            APIClient().get(detail_url(hotel))      # pause over: tries again
            assert get.call_count == 2


@pytest.mark.usefixtures('any_host')
class TestKey:
    def request(self, path='/api/v1/properties/1/', query='', language='en', host='a.example.com'):
        from django.test import RequestFactory
        request = RequestFactory().get(path + query, HTTP_HOST=host)
        request.LANGUAGE_CODE = language
        return request

    def test_it_changes_with_the_address_the_query_the_language_and_the_host(self):
        base = public_cache.key_for(self.request(), 'detail')
        assert base == public_cache.key_for(self.request(), 'detail')
        for changed in (
            self.request(path='/api/v1/properties/2/'), self.request(query='?page=2'),
            self.request(language='uz'), self.request(host='b.example.com'),
        ):
            assert public_cache.key_for(changed, 'detail') != base
        assert public_cache.key_for(self.request(), 'availability') != base

    def test_the_order_of_the_query_parameters_does_not_matter(self):
        assert (public_cache.key_for(self.request(query='?a=1&b=2'), 's')
                == public_cache.key_for(self.request(query='?b=2&a=1'), 's'))

    def test_it_is_short_and_has_no_characters_a_cache_server_dislikes(self):
        key = public_cache.key_for(self.request(query='?q=' + 'x' * 5000 + '%20%00 ü'), 'search')

        assert len(key) < 100 and key.isascii() and ' ' not in key
