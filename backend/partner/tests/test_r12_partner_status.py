"""
R12 phase 2: owner Status additions - hotel detail, series, reconciliation, arrivals, CSV.
Data: the status_world fixture (admin_panel/tests/status_fixtures.py).
"""
import csv
import io
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from admin_panel.tests.status_fixtures import make_booking
from common.dates import business_today

P = '/api/v1/partner/status'


def get_as(user, url, **params):
    client = APIClient()
    client.force_authenticate(user=user)
    return client.get(url, params)


def money(rows):
    return {row['currency']: row['amount'] for row in rows}


@pytest.mark.django_db
class TestSummaryAdditions:

    def test_new_fields(self, status_world):
        owner1 = status_world['owners'][0]
        data = get_as(owner1, f'{P}/', period='2026', granularity='month').data
        assert data['period_range'] == {'from': '2026-01-01', 'to': '2026-12-31'}
        assert (data['totals']['stayed'], data['totals']['unique_customers'], data['totals']['nights']) == (1, 3, 4)
        assert data['totals']['booking_status']['pending'] == 1
        assert len(data['series']) == 12
        assert data['reconciliation']['all_time']['counted'] == {'bookings': 5, 'guests': 5}
        alpha = data['properties'][0]
        assert (alpha['stayed'], alpha['unique_customers'], money(alpha['booking_value'])) == \
            (1, 2, {'USD': '450.00'})

    def test_invalid_granularity_is_400(self, status_world):
        assert get_as(status_world['owners'][0], f'{P}/', granularity='hour').status_code == 400


@pytest.mark.django_db
class TestHotelDetail:

    def test_own_hotel(self, status_world):
        owner1 = status_world['owners'][0]
        beta = status_world['hotels']['beta']
        data = get_as(owner1, f'{P}/hotels/{beta.id}/', granularity='year').data
        assert (data['hotel']['id'], data['hotel']['name']) == (beta.id, 'Beta Hotel')
        assert 'owner' not in data['hotel']
        assert (data['totals']['bookings'], money(data['totals']['revenue'])) == (2, {'EUR': '60.00', 'USD': '80.00'})
        assert [row['period'] for row in data['series']][:2] == ['2025', '2026']
        assert data['monthly'][3]['month'].endswith('-04')

    def test_other_owners_hotel_is_404(self, status_world):
        owner1 = status_world['owners'][0]
        delta = status_world['hotels']['delta']
        assert get_as(owner1, f'{P}/hotels/{delta.id}/').status_code == 404
        assert get_as(owner1, f'{P}/hotels/999999/').status_code == 404


@pytest.mark.django_db
class TestArrivals:

    def _arrivals(self, status_world):
        hotels = status_world['hotels']
        g1, g2, _ = status_world['guests']
        today = business_today()
        a = make_booking(g1, hotels['alpha'], today, '100.00')
        a.guest_full_name, a.guest_phone, a.special_requests = 'Aziz Karimov', '+998 90 333-12-34', 'Late arrival'
        a.save(update_fields=['guest_full_name', 'guest_phone', 'special_requests'])
        make_booking(g2, hotels['beta'], today + timedelta(days=1), '100.00')
        make_booking(g2, hotels['alpha'], today, '100.00', status='pending')
        make_booking(g2, hotels['alpha'], today, '100.00', status='cancelled')
        make_booking(g2, hotels['delta'], today, '100.00')                     # another owner's hotel
        return a

    def test_today(self, status_world):
        a = self._arrivals(status_world)
        response = get_as(status_world['owners'][0], f'{P}/arrivals/')
        assert response.status_code == 200
        assert (response.data['day'], response.data['date']) == ('today', business_today().isoformat())
        assert response.data['count'] == 1
        row = response.data['results'][0]
        assert (row['id'], row['reference'], row['guest_name'], row['special_requests']) == \
            (a.id, a.confirmation_code, 'Aziz Karimov', 'Late arrival')
        assert (row['property']['name'], row['rooms'], row['nights'], row['guests']) == ('Alpha Hotel', 1, 1, 1)
        assert row['phone_last4'] == '1234'
        assert 'email' not in str(row) and '333' not in str(row['phone_last4'])
        assert not any('@' in str(value) for value in row.values())

    def test_tomorrow_and_property_filter(self, status_world):
        self._arrivals(status_world)
        owner1 = status_world['owners'][0]
        hotels = status_world['hotels']
        assert get_as(owner1, f'{P}/arrivals/', day='tomorrow').data['count'] == 1
        assert get_as(owner1, f'{P}/arrivals/', property=hotels['beta'].id).data['count'] == 0
        assert get_as(owner1, f'{P}/arrivals/', property=hotels['delta'].id).status_code == 404
        assert get_as(owner1, f'{P}/arrivals/', day='yesterday').status_code == 400
        assert get_as(owner1, f'{P}/arrivals/', property='x').status_code == 400

    def test_other_owner_sees_only_own_arrivals(self, status_world):
        self._arrivals(status_world)
        rows = get_as(status_world['owners'][1], f'{P}/arrivals/').data['results']
        assert [row['property']['name'] for row in rows] == ['Delta Hotel']


@pytest.mark.django_db
class TestReconciliationCsv:

    def test_one_row_per_own_hotel_and_window(self, status_world):
        owner1 = status_world['owners'][0]
        response = get_as(owner1, f'{P}/', export='csv')
        body = b''.join(response.streaming_content).decode('utf-8')
        assert body.startswith('﻿')
        rows = list(csv.reader(io.StringIO(body[1:])))
        assert rows[0] == ['hotel_id', 'hotel', 'window', 'from', 'to', 'counted_bookings', 'counted_guests',
                           'stayed_bookings', 'stayed_guests']
        assert len(rows) == 1 + 2 * 5
        alpha_all = next(r for r in rows[1:] if r[1] == 'Alpha Hotel' and r[2] == 'all_time')
        assert alpha_all[5:] == ['3', '3', '1', '1']
        assert {r[1] for r in rows[1:]} == {'Alpha Hotel', 'Beta Hotel'}
        log = AdminAccessLog.objects.get(action='export_csv')
        assert (log.actor_id, log.details) == (owner1.id, {'export': 'partner_reconciliation', 'rows': 10})

    def test_query_count_is_constant(self, status_world, django_assert_max_num_queries):
        owner1 = status_world['owners'][0]
        for i in (5, 50):
            for j in range(i):
                make_booking(status_world['guests'][0], status_world['hotels']['beta'],
                             business_today() - timedelta(days=j + 1), '10.00', status='completed')
            with django_assert_max_num_queries(21):
                assert get_as(owner1, f'{P}/').status_code == 200


@pytest.mark.django_db
class TestInsights:

    def test_summary_and_hotel_detail_carry_the_insights(self, status_world):
        owner1 = status_world['owners'][0]
        beta = status_world['hotels']['beta']
        summary = get_as(owner1, f'{P}/', period='2026').data['insights']
        detail = get_as(owner1, f'{P}/hotels/{beta.id}/', period='2026').data['insights']
        for insights in (summary, detail):
            assert set(insights) == {'cancellation_rate', 'average_booking_value', 'average_stay_nights',
                                     'occupancy_rate', 'previous_period', 'change_pct'}
            assert insights['previous_period']['range'] == {'from': '2025-01-01', 'to': '2025-12-31'}
        assert summary['occupancy_rate'] is None

    def test_occupancy_uses_the_rooms_of_the_hotels_of_the_owner_only(self, status_world):
        from properties.models import RoomType
        owner1 = status_world['owners'][0]
        beta = status_world['hotels']['beta']
        RoomType.objects.create(property=beta, name='Std', slug='std', base_occupancy=2, max_occupancy=2,
                                base_price=1, total_rooms=10)
        data = get_as(owner1, f'{P}/hotels/{beta.id}/', period='2026').data['insights']
        assert data['occupancy_rate'] is not None
        assert float(data['occupancy_rate']) <= 100

    def test_all_time_has_no_comparison(self, status_world):
        data = get_as(status_world['owners'][0], f'{P}/').data['insights']
        assert data['previous_period'] is None and data['change_pct'] is None


@pytest.mark.django_db
class TestRegionRank:
    """Owner's anonymous rank among the active hotels of the region, by counted bookings."""

    def _more_hotels(self, status_world, count):
        from properties.models import Property
        alpha = status_world['hotels']['alpha']
        for n in range(count):
            Property.objects.create(
                owner=status_world['owners'][1], property_type=alpha.property_type, status='active', max_guests=2,
                address_line1=f'{n} Rank Street', country_ref=alpha.country_ref, region_ref=alpha.region_ref,
                city_ref=alpha.city_ref, city='Tashkent', base_price=1, currency='USD')

    def rank(self, status_world, hotel, **params):
        owner = status_world['owners'][0]
        return get_as(owner, f'{P}/hotels/{hotel.id}/', **params).data['rank']

    def test_hidden_when_the_region_has_fewer_than_five_hotels(self, status_world):
        self._more_hotels(status_world, 2)   # alpha, beta + 2 = 4
        assert self.rank(status_world, status_world['hotels']['alpha'], period='2026') is None

    def test_position_and_count_from_five_hotels(self, status_world):
        self._more_hotels(status_world, 3)   # 5 hotels
        alpha, beta = status_world['hotels']['alpha'], status_world['hotels']['beta']
        # 2026: alpha has 3 counted bookings, beta 1, the three new ones 0
        assert self.rank(status_world, alpha, period='2026') == {'position': 1, 'of': 5}
        assert self.rank(status_world, beta, period='2026') == {'position': 2, 'of': 5}

    def test_ties_share_the_position(self, status_world):
        self._more_hotels(status_world, 3)
        # 2025: only beta has a counted booking; alpha and the new hotels tie at 0 and share position 2
        assert self.rank(status_world, status_world['hotels']['beta'], period='2025') == {'position': 1, 'of': 5}
        assert self.rank(status_world, status_world['hotels']['alpha'], period='2025') == {'position': 2, 'of': 5}

    def test_nothing_about_other_hotels_is_returned(self, status_world):
        self._more_hotels(status_world, 3)
        owner = status_world['owners'][0]
        beta = status_world['hotels']['beta']
        data = get_as(owner, f'{P}/hotels/{beta.id}/', period='2026').data
        assert set(data['rank']) == {'position', 'of'}

    def test_hotel_without_a_region_has_no_rank(self, status_world):
        owner2 = status_world['owners'][1]
        gamma = status_world['hotels']['gamma']
        assert get_as(owner2, f'{P}/hotels/{gamma.id}/', period='2026').data['rank'] is None
