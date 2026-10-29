"""The hotel owner sees the ads of their own hotels: how they run, how many people saw and clicked, and the renewal question."""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from common.dates import business_today
from promotions import renewals
from promotions.models import AdRenewal, Promotion, PromotionDailyStat
from promotions.tests.helpers import make_guest, make_hotel, make_owner, make_promotion, make_staff

pytestmark = pytest.mark.django_db

URL = '/api/v1/partner/promotions/'


def client_of(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.fixture
def owner():
    return make_owner('mine@example.com')


@pytest.fixture
def hotel(owner):
    return make_hotel(owner, name='My Hotel')


def stats(promotion, impressions, clicks, days_ago=0):
    return PromotionDailyStat.objects.create(
        promotion=promotion, date=business_today() - timedelta(days=days_ago), impressions=impressions, clicks=clicks)


class TestTheList:
    def test_the_owner_sees_their_own_ads_with_views_clicks_and_click_rate(self, owner, hotel):
        promotion = make_promotion(hotel, start_offset=-3, days=30)
        stats(promotion, 300, 9)
        stats(promotion, 100, 3, days_ago=1)
        response = client_of(owner).get(URL)
        assert response.status_code == 200, response.data
        assert response.data['count'] == 1
        row = response.data['results'][0]
        assert (row['id'], row['status'], row['paid'], row['is_shown_now']) == (promotion.id, 'active', True, True)
        assert row['property'] == {'id': hotel.id, 'name': 'My Hotel'}
        assert (row['impressions'], row['clicks'], row['click_rate']) == (400, 12, '3.0')
        assert (row['start_date'], row['end_date']) == (promotion.start_date.isoformat(), promotion.end_date.isoformat())

    def test_the_click_rate_is_empty_before_the_first_view(self, owner, hotel):
        make_promotion(hotel)
        row = client_of(owner).get(URL).data['results'][0]
        assert (row['impressions'], row['clicks'], row['click_rate']) == (0, 0, None)

    def test_the_price_the_note_and_the_internal_fields_stay_private(self, owner, hotel):
        make_promotion(hotel, note='secret agreement 42', priority=90)
        row = client_of(owner).get(URL).data['results'][0]
        assert not {'price_amount', 'price_currency', 'note', 'priority', 'created_by', 'paid_marked_by'} & set(row)

    def test_another_owners_ads_are_not_shown(self, owner, hotel):
        make_promotion(hotel)
        stranger_hotel = make_hotel(make_owner('other@example.com'), name='Other Hotel')
        make_promotion(stranger_hotel)
        names = [row['property']['name'] for row in client_of(owner).get(URL).data['results']]
        assert names == ['My Hotel']

    def test_a_deleted_ad_is_not_shown(self, owner, hotel):
        make_promotion(hotel).soft_delete()
        assert client_of(owner).get(URL).data['count'] == 0

    def test_newest_first(self, owner, hotel):
        older = make_promotion(hotel, start_offset=-60, days=20, status='ended')
        newer = make_promotion(hotel, start_offset=-3, days=30)
        assert [row['id'] for row in client_of(owner).get(URL).data['results']] == [newer.id, older.id]

    def test_an_ad_of_a_suspended_hotel_says_why_it_is_not_shown(self, owner, hotel):
        make_promotion(hotel)
        hotel.status = 'suspended'
        hotel.save()
        row = client_of(owner).get(URL).data['results'][0]
        assert (row['is_shown_now'], row['blocked_reason']) == (False, 'hotel_not_active')

    def test_an_ad_not_yet_paid_is_not_shown(self, owner, hotel):
        make_promotion(hotel, paid=False, status='scheduled')
        row = client_of(owner).get(URL).data['results'][0]
        assert (row['paid'], row['is_shown_now']) == (False, False)


class TestFilters:
    def test_by_status_and_by_hotel(self, owner, hotel):
        second = make_hotel(owner, name='Second Hotel')
        running = make_promotion(hotel, start_offset=-3, days=30)
        finished = make_promotion(second, start_offset=-60, days=20, status='ended')
        api = client_of(owner)
        assert [row['id'] for row in api.get(URL, {'status': 'active'}).data['results']] == [running.id]
        assert [row['id'] for row in api.get(URL, {'property': second.id}).data['results']] == [finished.id]

    def test_a_wrong_status_or_property_value_is_a_400(self, owner, hotel):
        api = client_of(owner)
        assert api.get(URL, {'status': 'later'}).status_code == 400
        assert api.get(URL, {'property': 'abc'}).status_code == 400

    def test_another_owners_hotel_is_a_404(self, owner, hotel):
        stranger_hotel = make_hotel(make_owner('other@example.com'), name='Other Hotel')
        assert client_of(owner).get(URL, {'property': stranger_hotel.id}).status_code == 404


class TestTheRenewalQuestion:
    def end_today(self, hotel):
        promotion = make_promotion(hotel, start_offset=-29, days=30)
        renewals.open_due(today=promotion.end_date)
        return promotion

    def test_an_open_question_shows_until_when_the_ad_stays(self, owner, hotel, monkeypatch):
        promotion = self.end_today(hotel)
        monkeypatch.setattr('partner.promotions.business_today', lambda: promotion.end_date + timedelta(days=2))
        row = client_of(owner).get(URL).data['results'][0]
        deadline = promotion.end_date + timedelta(days=5)
        assert row['renewal'] == {'ends_on': promotion.end_date.isoformat(), 'deadline': deadline.isoformat(),
                                  'days_left': 3}

    def test_an_answered_question_is_not_shown(self, owner, hotel):
        promotion = self.end_today(hotel)
        AdRenewal.objects.filter(promotion=promotion).update(status='renewed')
        assert client_of(owner).get(URL).data['results'][0]['renewal'] is None

    def test_no_question_before_the_end_day(self, owner, hotel):
        make_promotion(hotel, start_offset=-3, days=30)
        assert client_of(owner).get(URL).data['results'][0]['renewal'] is None


class TestAccess:
    def test_a_guest_and_a_visitor_are_refused(self):
        assert client_of(make_guest()).get(URL).status_code == 403
        assert APIClient().get(URL).status_code in (401, 403)

    def test_staff_pass_the_permission_but_see_only_their_own_hotels(self, hotel):
        make_promotion(hotel)
        response = client_of(make_staff()).get(URL)
        assert response.status_code == 200 and response.data['count'] == 0

    def test_the_list_is_read_only(self, owner, hotel):
        assert client_of(owner).post(URL, {}, format='json').status_code == 405
        assert Promotion.objects.count() == 0
