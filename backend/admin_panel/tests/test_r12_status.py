"""
R12 phase 2: admin Status additions - flat hotels list, one guest's detail, hotel detail
series + reconciliation, CSV export, consistency between users and hotels.

Data: the status_world fixture (status_fixtures.py) plus bookings written here.
"""
import csv
import io
from datetime import timedelta
from decimal import Decimal

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from accounts.models import Review
from admin_panel.models import AdminAccessLog
from admin_panel.tests.status_fixtures import make_booking, make_payment
from common.dates import business_today
from payments.models import Refund
from users.models import User

S = '/api/v1/admin-panel/status'


@pytest.fixture
def staff(db):
    return User.objects.create_user(email='staff@example.com', password='StaffPassword#123', is_staff=True)


@pytest.fixture
def get(staff):
    client = APIClient()
    client.force_authenticate(user=staff)

    def _get(url, **params):
        return client.get(url, params)
    return _get


def money(rows):
    return {row['currency']: row['amount'] for row in rows}


def read_csv(response):
    body = b''.join(response.streaming_content).decode('utf-8')
    assert body.startswith('﻿')
    return list(csv.reader(io.StringIO(body[1:])))


@pytest.mark.django_db
class TestFlatHotelsList:

    def test_default_ordering_and_fields(self, get, status_world):
        h = status_world['hotels']
        response = get(f'{S}/hotels/')
        assert response.status_code == 200
        assert (response.data['period'], response.data['ordering'], response.data['count']) == ('all', '-bookings', 4)
        rows = response.data['results']
        assert [row['id'] for row in rows] == [h['alpha'].id, h['beta'].id, h['delta'].id, h['gamma'].id]
        alpha = rows[0]
        assert (alpha['rank'], alpha['name'], alpha['city'], alpha['country_code'], alpha['region']) == \
            (1, 'Alpha Hotel', 'Tashkent', 'UZ', 'Tashkent')
        assert (alpha['bookings'], alpha['stayed'], alpha['guests'], alpha['unique_customers'], alpha['nights']) == \
            (3, 1, 3, 2, 3)
        assert money(alpha['revenue']) == {'USD': '450.00'}
        assert money(alpha['booking_value']) == {'USD': '450.00'}
        assert alpha['rating'] is None
        # gamma: only a no-show (kept money is revenue, never a counted booking)
        assert (rows[3]['bookings'], money(rows[3]['revenue'])) == (0, {'USD': '999.00'})

    @pytest.mark.parametrize('ordering', ['price', 'name', '--bookings', 'revenue_uzs'])
    def test_unknown_ordering_is_400(self, get, status_world, ordering):
        response = get(f'{S}/hotels/', ordering=ordering)
        assert response.status_code == 400 and 'ordering' in response.data

    def test_revenue_ordering_uses_uzs_revenue(self, get, status_world):
        h = status_world['hotels']
        guest = status_world['guests'][0]
        day = business_today() - timedelta(days=40)
        big = make_booking(guest, h['gamma'], day, '10.00', status='completed')
        make_payment(big, '5000000', 'UZS')
        small = make_booking(guest, h['delta'], day, '10.00', status='completed')
        make_payment(small, '1000000', 'UZS')
        refunded = make_payment(make_booking(guest, h['beta'], day, '10.00', status='completed'), '9000000', 'UZS')
        Refund.objects.create(payment=refunded, booking=refunded.booking, amount=Decimal('8500000'), currency='UZS',
                              reason='staff', status='succeeded', idempotency_key='r-big')
        ids = [row['id'] for row in get(f'{S}/hotels/', ordering='-revenue').data['results']]
        assert ids == [h['gamma'].id, h['delta'].id, h['beta'].id, h['alpha'].id]
        ids = [row['id'] for row in get(f'{S}/hotels/', ordering='revenue').data['results']]
        assert ids[0] == h['alpha'].id and ids[-1] == h['gamma'].id

    def test_other_orderings(self, get, status_world):
        h = status_world['hotels']
        Review.objects.create(user=status_world['guests'][1], property=h['beta'], overall_rating=5, status='approved',
                              title='t', comment='c')
        Review.objects.create(user=status_world['guests'][0], property=h['alpha'], overall_rating=3,
                              status='approved', title='t', comment='c')
        Review.objects.create(user=status_world['guests'][2], property=h['alpha'], overall_rating=1,
                              status='pending', title='t', comment='c')
        rows = get(f'{S}/hotels/', ordering='-rating').data['results']
        assert [(row['id'], row['rating']) for row in rows[:2]] == [(h['beta'].id, '5.00'), (h['alpha'].id, '3.00')]
        assert rows[2]['rating'] is None
        ids = [row['id'] for row in get(f'{S}/hotels/', ordering='created_at').data['results']]
        assert ids == [h['alpha'].id, h['beta'].id, h['gamma'].id, h['delta'].id]
        assert get(f'{S}/hotels/', ordering='-guests').data['results'][0]['id'] == h['alpha'].id
        assert get(f'{S}/hotels/', ordering='nights').status_code == 200

    @pytest.mark.parametrize('term, expected', [
        ('alpha', ['alpha']),                 # hotel name
        ('chirch', ['gamma']),                # city
        ('KZ', ['delta']),                    # country code
        ('Казах', ['delta']),                 # country name, Russian
        ('almaty city', ['delta']),           # region name
    ])
    def test_search(self, get, status_world, term, expected):
        h = status_world['hotels']
        ids = {row['id'] for row in get(f'{S}/hotels/', search=term).data['results']}
        assert ids == {h[name].id for name in expected}

    def test_filters(self, get, status_world):
        h = status_world['hotels']
        assert {r['id'] for r in get(f'{S}/hotels/', country='uz').data['results']} == \
            {h['alpha'].id, h['beta'].id, h['gamma'].id}
        region = h['alpha'].region_ref_id
        assert {r['id'] for r in get(f'{S}/hotels/', region=str(region)).data['results']} == \
            {h['alpha'].id, h['beta'].id}
        assert {r['id'] for r in get(f'{S}/hotels/', country='UZ', region='unspecified').data['results']} == \
            {h['gamma'].id}
        h['delta'].status = 'suspended'
        h['delta'].save()
        assert [r['id'] for r in get(f'{S}/hotels/', status='suspended').data['results']] == [h['delta'].id]
        assert get(f'{S}/hotels/', status='closed').status_code == 400

    def test_page_size_is_capped(self, get, status_world):
        response = get(f'{S}/hotels/', page_size=1000)
        assert response.status_code == 200 and len(response.data['results']) == 4

    def test_period_and_custom_range(self, get, status_world):
        response = get(f'{S}/hotels/', period='custom', **{'from': '2026-04-01', 'to': '2026-04-30'})
        assert response.data['period_range'] == {'from': '2026-04-01', 'to': '2026-04-30'}
        alpha = response.data['results'][0]
        assert (alpha['bookings'], money(alpha['revenue'])) == (2, {'USD': '350.00'})
        for params in ({'period': 'custom', 'from': '2026-05-01', 'to': '2026-04-01'},
                       {'period': 'custom', 'from': '2000-01-01', 'to': '2026-01-01'},
                       {'period': 'custom', 'from': 'x', 'to': '2026-01-01'},
                       {'period': 'custom'}):
            assert get(f'{S}/hotels/', **params).status_code == 400

    def test_csv_export(self, get, status_world, staff):
        response = get(f'{S}/hotels/', export='csv', ordering='-bookings')
        assert response.status_code == 200
        assert response['Content-Type'].startswith('text/csv')
        rows = read_csv(response)
        assert rows[0][:3] == ['rank', 'id', 'name']
        assert [row[2] for row in rows[1:]] == ['Alpha Hotel', 'Beta Hotel', 'Delta Hotel', 'Gamma Hotel']
        assert rows[1][-2] == 'USD 450.00'
        log = AdminAccessLog.objects.get(action='export_csv')
        assert (log.actor_id, log.details) == (staff.id, {'export': 'status_hotels', 'rows': 4})

    def test_csv_same_filters_as_json(self, get, status_world):
        rows = read_csv(get(f'{S}/hotels/', export='csv', country='KZ'))
        assert [row[2] for row in rows[1:]] == ['Delta Hotel']


@pytest.mark.django_db
class TestUserDetail:

    def test_totals_hotels_and_history(self, get, status_world, staff):
        g1 = status_world['guests'][0]
        h = status_world['hotels']
        response = get(f'{S}/users/{g1.id}/')
        assert response.status_code == 200
        data = response.data
        assert (data['user']['id'], data['user']['email'], data['user']['phone']) == \
            (g1.id, 'guest1@example.com', '+998903330001')
        totals = data['totals']
        assert (totals['bookings'], totals['stayed'], totals['guests'], totals['nights']) == (2, 1, 2, 2)
        assert money(totals['revenue']) == {'USD': '250.00'}
        assert data['hotels_visited'] == 1
        assert [(row['id'], row['bookings'], row['stayed'], row['nights'], row['guests'], money(row['spent']))
                for row in data['hotels']] == [(h['alpha'].id, 2, 1, 2, 2, {'USD': '250.00'})]
        history = data['history']
        # every status except soft-deleted, newest check-in first
        assert history['count'] == 2
        first = history['results'][0]
        assert (first['check_in'], first['status'], first['hotel']['name'], first['total_price']) == \
            ('2026-04-10', 'completed', 'Alpha Hotel', '150.00')
        assert money(first['paid']) == {'USD': '150.00'} and first['refunded'] == []
        log = AdminAccessLog.objects.get(action='status_user_view')
        assert (log.actor_id, log.target_user_id) == (staff.id, g1.id)

    def test_history_includes_cancelled_and_pending(self, get, status_world):
        g3 = status_world['guests'][2]
        statuses = sorted(row['status'] for row in get(f'{S}/users/{g3.id}/').data['history']['results'])
        assert statuses == ['cancelled', 'confirmed', 'confirmed', 'no_show', 'pending']

    def test_period(self, get, status_world):
        g2 = status_world['guests'][1]
        data = get(f'{S}/users/{g2.id}/', period='2025').data
        assert (data['totals']['bookings'], data['history']['count']) == (1, 1)
        assert data['period_range'] == {'from': '2025-01-01', 'to': '2025-12-31'}

    def test_unknown_or_deleted_user_is_404_and_not_logged(self, get, status_world):
        g1 = status_world['guests'][0]
        g1.is_deleted = True
        g1.save()
        assert get(f'{S}/users/{g1.id}/').status_code == 404
        assert get(f'{S}/users/999999/').status_code == 404
        assert not AdminAccessLog.objects.filter(action='status_user_view').exists()

    def test_history_csv_neutralises_formulas(self, get, status_world):
        g1 = status_world['guests'][0]
        h = status_world['hotels']
        h['alpha'].translations.filter(language='en').update(name='=HYPERLINK("http://x")')
        rows = read_csv(get(f'{S}/users/{g1.id}/', export='csv'))
        assert rows[0][:4] == ['booking_id', 'reference', 'hotel_id', 'hotel']
        assert {row[3] for row in rows[1:]} == {'\'=HYPERLINK("http://x")'}
        assert AdminAccessLog.objects.get(action='export_csv').details == \
            {'export': f'status_user_{g1.id}_history', 'rows': 2}

    @override_settings(CSV_EXPORT_MAX_ROWS=1)
    def test_csv_is_truncated_after_max_rows(self, get, status_world):
        g1 = status_world['guests'][0]
        rows = read_csv(get(f'{S}/users/{g1.id}/', export='csv'))
        assert len(rows) == 3 and rows[-1] == ['truncated']
        assert AdminAccessLog.objects.get(action='export_csv').details['rows'] == 1


@pytest.mark.django_db
class TestUsersRanking:

    def test_new_fields_and_csv(self, get, status_world):
        rows = get(f'{S}/users/').data['results']
        assert (rows[0]['guests'], rows[0]['nights']) == (2, 2)
        csv_rows = read_csv(get(f'{S}/users/', export='csv'))
        assert csv_rows[0] == ['rank', 'id', 'full_name', 'phone', 'email', 'bookings', 'guests', 'nights',
                               'total_spent', 'last_booking_date']
        assert len(csv_rows) == 4
        # the phone starts with "+": neutralised for spreadsheets
        assert csv_rows[1][3] == "'+998903330002"


@pytest.mark.django_db
class TestHotelDetailAdditions:

    def test_booking_status_series_and_reconciliation(self, get, status_world):
        alpha = status_world['hotels']['alpha']
        data = get(f'{S}/hotels/{alpha.id}/', period='2026', granularity='month').data
        assert data['totals']['booking_status'] == {
            'pending': 1, 'confirmed': 2, 'completed': 1, 'cancelled': 1, 'expired': 0,
            'no_show': 0, 'no_show_reported': 0,
        }
        assert data['granularity'] == 'month' and len(data['series']) == 12
        april = data['series'][3]
        assert (april['period'], april['bookings'], april['guests'], april['stayed']) == ('2026-04', 2, 2, 1)
        assert set(data['reconciliation']) == {'today', 'this_week', 'this_month', 'this_year', 'all_time'}
        assert data['reconciliation']['all_time']['counted'] == {'bookings': 3, 'guests': 3}
        assert data['reconciliation']['all_time']['stayed'] == {'bookings': 1, 'guests': 1}

    def test_too_many_buckets_is_400(self, get, status_world):
        alpha = status_world['hotels']['alpha']
        response = get(f'{S}/hotels/{alpha.id}/', period='last_10_years', granularity='day')
        assert response.status_code == 400 and 'granularity' in response.data
        assert get(f'{S}/hotels/{alpha.id}/', granularity='hour').status_code == 400


@pytest.mark.django_db
class TestConsistency:
    """For one period, the sum over all users == the sum over all hotels."""

    @pytest.mark.parametrize('period', ['all', '2026', '2026-04', '2025'])
    def test_users_and_hotels_add_up(self, get, status_world, period):
        hotels = get(f'{S}/hotels/', period=period, page_size=100).data['results']
        users = get(f'{S}/users/', period=period, page_size=100).data['results']
        assert sum(r['bookings'] for r in hotels) == sum(r['bookings'] for r in users)
        assert sum(r['guests'] for r in hotels) == sum(r['guests'] for r in users)
        assert sum(r['nights'] for r in hotels) == sum(r['nights'] for r in users)

        def per_currency(rows, field):
            total = {}
            for row in rows:
                for entry in row[field]:
                    total[entry['currency']] = total.get(entry['currency'], Decimal('0')) + Decimal(entry['amount'])
            return total
        assert per_currency(hotels, 'revenue') == per_currency(users, 'total_spent')

    def test_user_per_hotel_row_matches_the_hotel_filtered_to_that_user(self, get, status_world):
        g2 = status_world['guests'][1]
        alpha = status_world['hotels']['alpha']
        row = next(r for r in get(f'{S}/users/{g2.id}/').data['hotels'] if r['id'] == alpha.id)
        assert (row['bookings'], row['guests'], money(row['spent'])) == (1, 1, {'USD': '200.00'})


@pytest.mark.django_db
class TestQueryCountIsConstant:

    def _grow(self, status_world, n):
        guest = status_world['guests'][0]
        for i in range(n):
            make_booking(guest, status_world['hotels']['beta'], business_today() - timedelta(days=i + 1),
                         '10.00', status='completed')

    @pytest.mark.parametrize('n', [5, 50])
    def test_hotels_list(self, get, status_world, n, django_assert_max_num_queries):
        self._grow(status_world, n)
        # fully refunded ids, UZS revenue (payments, refunds), the list, revenue (payments, refunds),
        # booking value (the revenue sort is done on the list, so no COUNT query)
        with django_assert_max_num_queries(7):
            assert get(f'{S}/hotels/', ordering='-revenue').status_code == 200

    @pytest.mark.parametrize('n', [5, 50])
    def test_user_detail(self, get, status_world, n, django_assert_max_num_queries):
        self._grow(status_world, n)
        g1 = status_world['guests'][0]
        # user, refunded ids, history (count, page, paid, refunded), totals (counts, revenue x2,
        # value), per hotel, hotel names, spent (x2), audit insert
        with django_assert_max_num_queries(15):
            assert get(f'{S}/users/{g1.id}/').status_code == 200

    @pytest.mark.parametrize('n', [5, 50])
    def test_hotel_detail(self, get, status_world, n, django_assert_max_num_queries):
        self._grow(status_world, n)
        beta = status_world['hotels']['beta']
        # hotel, refunded ids, totals (4), series (span, counts, revenue x2), reconciliation, years,
        # monthly (3)
        with django_assert_max_num_queries(15):
            assert get(f'{S}/hotels/{beta.id}/').status_code == 200
