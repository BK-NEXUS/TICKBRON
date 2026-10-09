"""`promoted` key of /properties/search/: only paid, running promotions of hotels that match the query."""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from common.dates import business_today
from promotions import service
from promotions.tests.helpers import make_hotel, make_owner, make_promotion, make_superadmin, uz_city

pytestmark = pytest.mark.django_db
URL = '/api/v1/properties/search/'


def search(**params):
    response = APIClient().get(URL, params)
    assert response.status_code == 200, response.content
    return response.json()


def promoted_ids(body):
    return [item['id'] for item in body['promoted']]


@pytest.fixture
def cheap():
    return make_hotel(make_owner('cheap@example.com'), name='Cheap', base_price=100000)


@pytest.fixture
def pricey():
    return make_hotel(make_owner('pricey@example.com'), name='Pricey', base_price=900000)


def test_no_promotions_gives_empty_list(cheap):
    assert search()['promoted'] == []


def test_running_paid_promotion_is_returned_with_card_fields(cheap):
    promo = make_promotion(cheap)
    body = search()
    assert promoted_ids(body) == [cheap.pk]
    item = body['promoted'][0]
    assert item['promotion_id'] == promo.pk
    assert {'translations', 'primary_photo', 'average_rating', 'base_price', 'currency', 'city'} <= set(item)


def test_only_hotels_that_match_the_filters_are_returned(cheap, pricey):
    make_promotion(cheap)
    make_promotion(pricey)
    assert promoted_ids(search(max_price=200000)) == [cheap.pk]
    assert promoted_ids(search(min_price=500000)) == [pricey.pk]
    assert promoted_ids(search(min_price=2000000)) == []


def test_text_and_guest_filters_apply_too(cheap, pricey):
    make_promotion(cheap)
    make_promotion(pricey)
    assert promoted_ids(search(q='Pricey')) == [pricey.pk]
    assert promoted_ids(search(min_guests=5)) == []


def test_promotion_does_not_add_hotels_to_the_normal_results(cheap, pricey):
    before = search(max_price=200000)
    make_promotion(pricey)
    after = search(max_price=200000)
    assert after['count'] == before['count'] == 1
    assert [r['id'] for r in after['results']] == [cheap.pk]
    assert after['promoted'] == []


def test_promoted_hotel_stays_in_the_normal_list(cheap):
    make_promotion(cheap)
    body = search()
    assert body['count'] == 1
    assert [r['id'] for r in body['results']] == [cheap.pk]
    assert 'promotion_id' not in body['results'][0]


def test_only_first_page_has_banners(cheap, pricey):
    make_promotion(cheap)
    assert promoted_ids(search(page=1, page_size=1)) == [cheap.pk]
    assert search(page=2, page_size=1)['promoted'] == []


def test_sort_does_not_remove_banners(cheap):
    make_promotion(cheap)
    assert promoted_ids(search(sort='price_desc')) == [cheap.pk]


def test_unpaid_expired_future_and_paused_are_not_returned(cheap, pricey):
    make_promotion(cheap, paid=False)
    make_promotion(pricey, start_offset=-10, days=3)
    third = make_hotel(make_owner('third@example.com'), name='Third')
    make_promotion(third, start_offset=3)
    fourth = make_hotel(make_owner('fourth@example.com'), name='Fourth')
    make_promotion(fourth, status='paused')
    assert search()['promoted'] == []


def test_suspended_hotel_is_not_returned(cheap):
    make_promotion(cheap)
    cheap.status = 'suspended'
    cheap.save(update_fields=['status'])
    assert search()['promoted'] == []


def test_at_most_eight_banners_highest_priority_first():
    hotels = [make_hotel(make_owner(f'h{i}@example.com'), name=f'H{i}') for i in range(10)]
    for i, hotel in enumerate(hotels):
        make_promotion(hotel, priority=i)
    ids = promoted_ids(search())
    assert len(ids) == 8
    assert ids == [h.pk for h in reversed(hotels)][:8]


def test_promotion_scoped_to_a_city_needs_a_hotel_there():
    city = uz_city()
    inside = make_hotel(make_owner('in@example.com'), name='In', city_ref=city)
    outside = make_hotel(make_owner('out@example.com'), name='Out')
    make_promotion(inside, city_ref=city)
    make_promotion(outside, city_ref=city)
    assert promoted_ids(search()) == [inside.pk]


def test_service_created_promotion_is_returned_after_payment(cheap):
    admin = make_superadmin()
    first = business_today()
    promo = service.create_promotion(actor=admin, property=cheap, start_date=first,
                                     end_date=first + timedelta(days=6))
    assert search()['promoted'] == []
    service.mark_paid(promo, actor=admin)
    assert promoted_ids(search()) == [cheap.pk]


def test_invalid_params_still_return_400():
    response = APIClient().get(URL, {'min_price': 'abc'})
    assert response.status_code == 400
    assert 'promoted' not in response.json()
