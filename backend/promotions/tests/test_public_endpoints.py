"""Home carousel, click endpoint and the view/click counters with their per-visitor dedupe."""
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from common.dates import business_today
from promotions.models import PromotionDailyStat
from promotions.tests.helpers import make_hotel, make_owner, make_promotion, uz_city, other_country_city

pytestmark = pytest.mark.django_db
HOME = '/api/v1/promotions/home/'
SEARCH = '/api/v1/properties/search/'


def click_url(promotion):
    return f'/api/v1/promotions/{promotion.pk}/click/'


def visitor(ip='10.0.0.1'):
    return APIClient(REMOTE_ADDR=ip)


def stat(promotion):
    return PromotionDailyStat.objects.filter(promotion=promotion).first()


@pytest.fixture
def hotel():
    return make_hotel(make_owner('h@example.com'), name='Alpha')


@pytest.fixture
def promo(hotel):
    return make_promotion(hotel)


class TestHome:
    def test_returns_running_paid_promotions(self, promo):
        body = visitor().get(HOME).json()
        assert [item['promotion_id'] for item in body['results']] == [promo.pk]
        assert body['results'][0]['id'] == promo.property_id

    def test_hides_unpaid_and_inactive(self, hotel):
        make_promotion(hotel, paid=False)
        suspended = make_hotel(make_owner('s@example.com'), name='Sus', status='suspended')
        make_promotion(suspended)
        assert visitor().get(HOME).json()['results'] == []

    def test_at_most_eight(self):
        for i in range(10):
            make_promotion(make_hotel(make_owner(f'm{i}@example.com'), name=f'M{i}'), priority=i)
        results = visitor().get(HOME).json()['results']
        assert len(results) == 8
        assert results[0]['promotion_id'] > results[-1]['promotion_id']

    def test_country_filter(self):
        uz, foreign = uz_city(), other_country_city()
        local = make_promotion(make_hotel(make_owner('l@example.com'), name='Local', city_ref=uz))
        make_promotion(make_hotel(make_owner('f@example.com'), name='Foreign', city_ref=foreign))
        body = visitor().get(HOME, {'country': uz.region.country_id}).json()
        assert [item['promotion_id'] for item in body['results']] == [local.pk]

    @pytest.mark.parametrize('value', ['abc', '-1', '0'])
    def test_bad_country_is_400(self, value):
        assert visitor().get(HOME, {'country': value}).status_code == 400

    def test_is_public_and_read_only(self, promo):
        assert visitor().get(HOME).status_code == 200
        assert visitor().post(HOME).status_code == 405

    def test_counts_one_impression_per_visitor_per_hour(self, promo):
        visitor().get(HOME)
        visitor().get(HOME)
        assert stat(promo).impressions == 1
        visitor('10.0.0.2').get(HOME)
        assert stat(promo).impressions == 2

    def test_stat_row_uses_the_business_date(self, promo):
        visitor().get(HOME)
        assert stat(promo).date == business_today()


class TestSearchImpressions:
    def test_search_banner_counts_once_per_visitor(self, promo):
        visitor().get(SEARCH)
        visitor().get(SEARCH)
        assert stat(promo).impressions == 1

    def test_page_two_does_not_count(self, promo):
        visitor().get(SEARCH, {'page': 2})
        assert stat(promo) is None

    def test_non_matching_filter_does_not_count(self, promo):
        visitor().get(SEARCH, {'min_price': 99999999})
        assert stat(promo) is None


class TestClick:
    def test_click_is_counted_and_returns_204(self, promo):
        response = visitor().post(click_url(promo))
        assert response.status_code == 204
        assert stat(promo).clicks == 1

    def test_same_visitor_is_counted_once_per_hour(self, promo):
        visitor().post(click_url(promo))
        visitor().post(click_url(promo))
        assert stat(promo).clicks == 1

    def test_other_visitor_counts_separately(self, promo):
        visitor().post(click_url(promo))
        visitor('10.0.0.9').post(click_url(promo))
        assert stat(promo).clicks == 2

    def test_clicks_and_impressions_are_independent(self, promo):
        visitor().get(HOME)
        visitor().post(click_url(promo))
        row = stat(promo)
        assert (row.impressions, row.clicks) == (1, 1)

    def test_unknown_unpaid_or_expired_promotion_is_404_and_not_counted(self, hotel):
        unpaid = make_promotion(hotel, paid=False)
        assert visitor().post(click_url(unpaid)).status_code == 404
        assert stat(unpaid) is None
        missing = type('P', (), {'pk': 987654})
        assert visitor().post(click_url(missing)).status_code == 404

    def test_get_is_not_allowed(self, promo):
        assert visitor().get(click_url(promo)).status_code == 405


class TestCacheDown:
    def test_search_still_works_and_nothing_is_counted(self, promo):
        with patch('promotions.stats.cache.add', side_effect=ConnectionError('redis down')):
            response = visitor().get(SEARCH)
        assert response.status_code == 200
        assert len(response.json()['promoted']) == 1
        assert stat(promo) is None

    def test_click_returns_204_and_counts_nothing(self, promo):
        with patch('promotions.stats.cache.add', side_effect=ConnectionError('redis down')):
            assert visitor().post(click_url(promo)).status_code == 204
        assert stat(promo) is None


class TestPrivacy:
    def test_cache_key_holds_no_raw_ip(self, promo):
        with patch('promotions.stats.cache.add', return_value=True) as add:
            visitor('203.0.113.77').get(HOME)
        key = add.call_args.args[0]
        assert '203.0.113.77' not in key
        assert key.startswith('promo:impression:')

    def test_stat_table_has_no_visitor_columns(self):
        names = {field.name for field in PromotionDailyStat._meta.get_fields()}
        assert names == {'id', 'promotion', 'date', 'impressions', 'clicks'}


class TestThrottle:
    @patch('promotions.views.TESTING', False)
    def test_click_is_rate_limited(self):
        codes = [visitor('10.9.9.9').post('/api/v1/promotions/987654/click/').status_code for _ in range(61)]
        assert codes[-1] == 429
        assert set(codes[:-1]) == {404}
