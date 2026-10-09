"""Super-admin promotion API: find a hotel, create and manage promotions, read statistics."""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from common.dates import business_today
from promotions.models import Promotion, PromotionDailyStat
from promotions.tests.helpers import (
    make_guest, make_hotel, make_owner, make_promotion, make_staff, make_superadmin, uz_city)

pytestmark = pytest.mark.django_db
A = '/api/v1/admin-panel'
today = business_today


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin():
    return client_for(make_superadmin())


@pytest.fixture
def staff():
    return client_for(make_staff())


@pytest.fixture
def hotel():
    return make_hotel(make_owner('o@example.com'), name='Registan Plaza', city_ref=uz_city())


def payload(hotel, start=0, days=7, **extra):
    first = today() + timedelta(days=start)
    return {'property': hotel.pk, 'start_date': first.isoformat(),
            'end_date': (first + timedelta(days=days - 1)).isoformat(), **extra}


class TestHotelSearch:
    def test_finds_hotel_by_name(self, admin, hotel):
        make_hotel(make_owner('x@example.com'), name='Other Hotel')
        body = admin.get(f'{A}/promotion-hotels/', {'q': 'registan'}).json()
        assert [row['id'] for row in body['results']] == [hotel.pk]
        row = body['results'][0]
        assert row['name'] == 'Registan Plaza'
        assert row['status'] == 'active'
        assert row['has_running_promotion'] is False

    def test_flags_hotel_with_a_promotion(self, admin, hotel):
        make_promotion(hotel)
        row = admin.get(f'{A}/promotion-hotels/', {'q': 'registan'}).json()['results'][0]
        assert row['has_running_promotion'] is True

    def test_short_query_returns_nothing(self, admin, hotel):
        assert admin.get(f'{A}/promotion-hotels/', {'q': 'r'}).json()['results'] == []
        assert admin.get(f'{A}/promotion-hotels/').json()['results'] == []

    def test_lists_suspended_hotels_too(self, admin):
        make_hotel(make_owner('s@example.com'), name='Sleepy Inn', status='suspended')
        rows = admin.get(f'{A}/promotion-hotels/', {'q': 'sleepy'}).json()['results']
        assert rows[0]['status'] == 'suspended'

    def test_owner_contact_data_is_not_returned(self, admin, hotel):
        text = admin.get(f'{A}/promotion-hotels/', {'q': 'registan'}).content.decode()
        assert 'o@example.com' not in text

    def test_staff_can_search(self, staff, hotel):
        assert staff.get(f'{A}/promotion-hotels/', {'q': 'registan'}).status_code == 200


class TestCreate:
    def test_creates_unpaid_promotion(self, admin, hotel):
        response = admin.post(f'{A}/promotions/', payload(hotel, priority=10, price_amount='2500000',
                                                           price_currency='UZS', note='Invoice 7'), format='json')
        assert response.status_code == 201, response.content
        body = response.json()
        assert body['status'] == 'scheduled'
        assert body['paid'] is False
        assert body['priority'] == 10
        assert body['property']['id'] == hotel.pk
        assert body['property']['name'] == 'Registan Plaza'
        assert body['is_shown_now'] is False
        assert AdminAccessLog.objects.filter(action='promotion_create').count() == 1

    def test_scope_is_saved(self, admin, hotel):
        city = uz_city()
        response = admin.post(f'{A}/promotions/', payload(hotel, city_ref=city.pk), format='json')
        assert response.status_code == 201
        assert response.json()['city_ref'] == city.pk

    def test_overlap_is_400_with_code(self, admin, hotel):
        admin.post(f'{A}/promotions/', payload(hotel), format='json')
        response = admin.post(f'{A}/promotions/', payload(hotel, start=3), format='json')
        assert response.status_code == 400
        assert response.json()['code'] == 'overlap'

    def test_past_start_is_400(self, admin, hotel):
        response = admin.post(f'{A}/promotions/', payload(hotel, start=-2), format='json')
        assert (response.status_code, response.json()['code']) == (400, 'start_in_past')

    @pytest.mark.parametrize('field,value', [
        ('property', 999999), ('property', 'x'), ('start_date', 'tomorrow'), ('priority', 'high'),
        ('price_amount', 'abc'), ('city_ref', 999999)])
    def test_invalid_input_is_400(self, admin, hotel, field, value):
        body = payload(hotel)
        body[field] = value
        assert admin.post(f'{A}/promotions/', body, format='json').status_code == 400

    def test_missing_dates_is_400(self, admin, hotel):
        assert admin.post(f'{A}/promotions/', {'property': hotel.pk}, format='json').status_code == 400

    def test_status_and_paid_cannot_be_set_on_create(self, admin, hotel):
        response = admin.post(f'{A}/promotions/', payload(hotel, status='active', paid=True,
                                                           paid_at='2026-01-01T00:00:00Z'), format='json')
        body = response.json()
        assert (body['status'], body['paid']) == ('scheduled', False)

    def test_staff_cannot_create(self, staff, hotel):
        assert staff.post(f'{A}/promotions/', payload(hotel), format='json').status_code == 403
        assert Promotion.objects.count() == 0


class TestList:
    def test_lists_with_totals_and_pagination(self, admin, hotel):
        promo = make_promotion(hotel)
        PromotionDailyStat.objects.create(promotion=promo, date=today(), impressions=40, clicks=4)
        body = admin.get(f'{A}/promotions/').json()
        assert body['count'] == 1
        row = body['results'][0]
        assert (row['total_impressions'], row['total_clicks']) == (40, 4)
        assert row['paid'] is True and row['is_shown_now'] is True

    def test_filters(self, admin, hotel):
        other = make_hotel(make_owner('b@example.com'), name='Bukhara Palace')
        paid = make_promotion(hotel)
        unpaid = make_promotion(other, paid=False)
        ids = lambda **q: {r['id'] for r in admin.get(f'{A}/promotions/', q).json()['results']}
        assert ids(q='bukhara') == {unpaid.pk}
        assert ids(paid='true') == {paid.pk}
        assert ids(paid='false') == {unpaid.pk}
        assert ids(status='scheduled') == set()
        assert ids(status='active') == {paid.pk, unpaid.pk}

    def test_name_search_does_not_inflate_totals_with_several_translations(self, admin, hotel):
        from properties.models import PropertyTranslation
        PropertyTranslation.objects.create(property=hotel, language='ru', name='Registan Plaza RU')
        PropertyTranslation.objects.create(property=hotel, language='uz', name='Registan Plaza UZ')
        promo = make_promotion(hotel)
        PromotionDailyStat.objects.create(promotion=promo, date=today(), impressions=40, clicks=4)
        body = admin.get(f'{A}/promotions/', {'q': 'registan'}).json()
        assert body['count'] == 1
        assert (body['results'][0]['total_impressions'], body['results'][0]['total_clicks']) == (40, 4)

    def test_date_filter_matches_overlapping_periods(self, admin, hotel):
        promo = make_promotion(hotel, start_offset=10, days=5)
        ids = lambda **q: {r['id'] for r in admin.get(f'{A}/promotions/', q).json()['results']}
        assert ids(**{'from': (today() + timedelta(days=14)).isoformat()}) == {promo.pk}
        assert ids(**{'from': (today() + timedelta(days=16)).isoformat()}) == set()
        assert ids(to=(today() + timedelta(days=9)).isoformat()) == set()

    def test_ordering_by_clicks(self, admin, hotel):
        other = make_hotel(make_owner('b@example.com'), name='Bukhara Palace')
        low, high = make_promotion(hotel), make_promotion(other)
        PromotionDailyStat.objects.create(promotion=high, date=today(), impressions=9, clicks=5)
        rows = admin.get(f'{A}/promotions/', {'ordering': '-clicks'}).json()['results']
        assert [r['id'] for r in rows] == [high.pk, low.pk]

    @pytest.mark.parametrize('query', [{'status': 'nope'}, {'paid': 'maybe'}, {'from': 'x'}, {'ordering': 'secret'}])
    def test_bad_filters_are_400(self, admin, query):
        assert admin.get(f'{A}/promotions/', query).status_code == 400

    def test_suspended_hotel_is_marked_blocked(self, admin, hotel):
        make_promotion(hotel)
        hotel.status = 'suspended'
        hotel.save(update_fields=['status'])
        row = admin.get(f'{A}/promotions/').json()['results'][0]
        assert row['blocked_reason'] == 'hotel_not_active'
        assert row['is_shown_now'] is False

    def test_scope_mismatch_is_marked_blocked(self, admin):
        outside = make_hotel(make_owner('c@example.com'), name='Out')
        make_promotion(outside, city_ref=uz_city())
        assert admin.get(f'{A}/promotions/').json()['results'][0]['blocked_reason'] == 'outside_scope'

    def test_deleted_promotions_are_hidden(self, admin, hotel):
        make_promotion(hotel).soft_delete()
        assert admin.get(f'{A}/promotions/').json()['count'] == 0

    def test_staff_can_read(self, staff, hotel):
        make_promotion(hotel)
        assert staff.get(f'{A}/promotions/').json()['count'] == 1


class TestDetailAndUpdate:
    def test_detail(self, admin, hotel):
        promo = make_promotion(hotel)
        assert admin.get(f'{A}/promotions/{promo.pk}/').json()['id'] == promo.pk

    def test_unknown_is_404(self, admin):
        assert admin.get(f'{A}/promotions/999999/').status_code == 404
        assert admin.patch(f'{A}/promotions/999999/', {'priority': 1}, format='json').status_code == 404

    def test_patch_changes_priority_and_note(self, admin, hotel):
        promo = make_promotion(hotel)
        response = admin.patch(f'{A}/promotions/{promo.pk}/', {'priority': 80, 'note': 'VIP'}, format='json')
        assert response.status_code == 200
        promo.refresh_from_db()
        assert (promo.priority, promo.note) == (80, 'VIP')
        assert AdminAccessLog.objects.filter(action='promotion_update').count() == 1

    def test_patch_dates_rechecks_overlap(self, admin, hotel):
        make_promotion(hotel, start_offset=0, days=7)
        later = make_promotion(hotel, start_offset=7, days=7)
        response = admin.patch(f'{A}/promotions/{later.pk}/',
                               {'start_date': (today() + timedelta(days=3)).isoformat()}, format='json')
        assert (response.status_code, response.json()['code']) == (400, 'overlap')

    def test_patch_cannot_touch_money_status_or_hotel(self, admin, hotel):
        promo = make_promotion(hotel, paid=False)
        other = make_hotel(make_owner('d@example.com'), name='Other')
        admin.patch(f'{A}/promotions/{promo.pk}/',
                    {'status': 'ended', 'paid_at': '2026-01-01T00:00:00Z', 'property': other.pk}, format='json')
        promo.refresh_from_db()
        assert (promo.status, promo.paid_at, promo.property_id) == ('active', None, hotel.pk)

    def test_empty_patch_is_400(self, admin, hotel):
        promo = make_promotion(hotel)
        assert admin.patch(f'{A}/promotions/{promo.pk}/', {}, format='json').status_code == 400

    def test_staff_cannot_patch(self, staff, hotel):
        promo = make_promotion(hotel)
        assert staff.patch(f'{A}/promotions/{promo.pk}/', {'priority': 1}, format='json').status_code == 403


class TestActions:
    def test_mark_paid_makes_it_shown(self, admin, hotel):
        created = admin.post(f'{A}/promotions/', payload(hotel), format='json').json()
        response = admin.post(f'{A}/promotions/{created["id"]}/mark-paid/')
        assert response.status_code == 200
        assert response.json()['paid'] is True and response.json()['is_shown_now'] is True
        again = admin.post(f'{A}/promotions/{created["id"]}/mark-paid/')
        assert (again.status_code, again.json()['code']) == (400, 'already_paid')

    def test_pause_resume_cancel(self, admin, hotel):
        promo = make_promotion(hotel)
        assert admin.post(f'{A}/promotions/{promo.pk}/pause/').json()['status'] == 'paused'
        assert admin.post(f'{A}/promotions/{promo.pk}/resume/').json()['status'] == 'active'
        response = admin.post(f'{A}/promotions/{promo.pk}/cancel/', {'reason': 'Client asked'}, format='json')
        assert response.json()['status'] == 'cancelled'
        assert response.json()['cancelled_reason'] == 'Client asked'

    def test_cancel_without_reason_is_400(self, admin, hotel):
        promo = make_promotion(hotel)
        response = admin.post(f'{A}/promotions/{promo.pk}/cancel/', {}, format='json')
        assert (response.status_code, response.json()['code']) == (400, 'reason_required')

    def test_wrong_state_is_400(self, admin, hotel):
        promo = make_promotion(hotel, status='ended')
        assert admin.post(f'{A}/promotions/{promo.pk}/pause/').status_code == 400

    @pytest.mark.parametrize('action', ['pause', 'resume', 'cancel', 'mark-paid'])
    def test_unknown_promotion_is_404(self, admin, action):
        assert admin.post(f'{A}/promotions/999999/{action}/', {'reason': 'x'}, format='json').status_code == 404

    @pytest.mark.parametrize('action', ['pause', 'resume', 'cancel', 'mark-paid'])
    def test_staff_cannot_run_actions(self, staff, hotel, action):
        promo = make_promotion(hotel)
        assert staff.post(f'{A}/promotions/{promo.pk}/{action}/', {'reason': 'x'}, format='json').status_code == 403

    def test_audit_rows_record_the_actor(self, admin, hotel):
        promo = make_promotion(hotel, paid=False)
        admin.post(f'{A}/promotions/{promo.pk}/mark-paid/')
        row = AdminAccessLog.objects.get(action='promotion_mark_paid')
        assert row.details['promotion_id'] == promo.pk


class TestStats:
    def test_daily_rows_totals_and_ctr(self, admin, hotel):
        promo = make_promotion(hotel)
        PromotionDailyStat.objects.create(promotion=promo, date=today() - timedelta(days=1), impressions=200, clicks=10)
        PromotionDailyStat.objects.create(promotion=promo, date=today(), impressions=100, clicks=5)
        body = admin.get(f'{A}/promotions/{promo.pk}/stats/').json()
        assert [r['impressions'] for r in body['days']] == [200, 100]
        assert body['days'][0]['ctr'] == 5.0
        assert body['totals'] == {'impressions': 300, 'clicks': 15, 'ctr': 5.0}

    def test_range_filter(self, admin, hotel):
        promo = make_promotion(hotel)
        PromotionDailyStat.objects.create(promotion=promo, date=today() - timedelta(days=5), impressions=1, clicks=0)
        PromotionDailyStat.objects.create(promotion=promo, date=today(), impressions=2, clicks=1)
        body = admin.get(f'{A}/promotions/{promo.pk}/stats/', {'from': today().isoformat()}).json()
        assert [r['impressions'] for r in body['days']] == [2]

    def test_no_impressions_gives_null_ctr(self, admin, hotel):
        promo = make_promotion(hotel)
        body = admin.get(f'{A}/promotions/{promo.pk}/stats/').json()
        assert body['days'] == [] and body['totals']['ctr'] is None

    def test_bad_dates_and_unknown_id(self, admin, hotel):
        promo = make_promotion(hotel)
        assert admin.get(f'{A}/promotions/{promo.pk}/stats/', {'from': 'x'}).status_code == 400
        assert admin.get(f'{A}/promotions/999999/stats/').status_code == 404

    def test_staff_can_read_stats(self, staff, hotel):
        promo = make_promotion(hotel)
        assert staff.get(f'{A}/promotions/{promo.pk}/stats/').status_code == 200


class TestRoles:
    @pytest.mark.parametrize('method,path', [
        ('get', 'promotions/'), ('post', 'promotions/'), ('get', 'promotion-hotels/'),
        ('get', 'promotions/1/'), ('post', 'promotions/1/mark-paid/')])
    def test_anonymous_owner_and_guest_are_refused(self, method, path):
        for user in (None, make_guest(), make_owner('ow@example.com')):
            client = APIClient()
            if user:
                client.force_authenticate(user=user)
            assert getattr(client, method)(f'{A}/{path}').status_code in (401, 403)
