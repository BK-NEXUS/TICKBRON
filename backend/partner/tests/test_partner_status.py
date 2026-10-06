"""
Partner Status: an owner's own numbers only (Status plan S4).

GET /api/v1/partner/status/?period=all|YYYY|YYYY-MM&year=YYYY
Access is covered by test_access_matrix.py. Data: the status_world fixture (admin_panel/tests/status_fixtures.py).
"""
import pytest
from rest_framework.test import APIClient

from users.models import User

URL = '/api/v1/partner/status/'


def get_as(user, **params):
    client = APIClient()
    client.force_authenticate(user=user)
    return client.get(URL, params)


def revenue(row):
    return {item['currency']: item['amount'] for item in row['revenue']}


@pytest.mark.django_db
class TestPartnerStatus:

    def test_summary_since_the_account_was_created(self, status_world):
        owner1 = status_world['owners'][0]

        response = get_as(owner1, year=2026)

        assert response.status_code == 200
        assert response.data['since'] == owner1.date_joined.date().isoformat()
        assert response.data['period'] == 'all'
        totals = response.data['totals']
        assert (totals['bookings'], totals['guests'], revenue(totals)) == \
            (5, 5, {'EUR': '60.00', 'USD': '530.00'})  # R12: guests = persons (SUM guest_count), was distinct accounts (was 3)

    def test_per_property_breakdown_lists_only_own_hotels(self, status_world):
        owner1 = status_world['owners'][0]
        hotels = status_world['hotels']

        rows = get_as(owner1).data['properties']

        assert [(row['id'], row['name'], row['bookings'], row['guests']) for row in rows] == [
            (hotels['alpha'].id, 'Alpha Hotel', 3, 3),  # R12: guests = persons (SUM guest_count), was distinct accounts (was 2)
            (hotels['beta'].id, 'Beta Hotel', 2, 2),
        ]
        assert revenue(rows[1]) == {'EUR': '60.00', 'USD': '80.00'}
        assert (rows[0]['city'], rows[0]['region'], rows[0]['country']) == ('Tashkent', 'Tashkent', 'Uzbekistan')

    def test_monthly_series(self, status_world):
        owner1 = status_world['owners'][0]

        response = get_as(owner1, year=2026)

        assert (response.data['year'], response.data['available_years']) == (2026, [2025, 2026])
        months = {row['month']: row for row in response.data['monthly']}
        assert len(months) == 12
        assert (months['2026-04']['bookings'], months['2026-04']['guests'], revenue(months['2026-04'])) == \
            (3, 3, {'EUR': '60.00', 'USD': '350.00'})
        assert months['2026-01']['bookings'] == 0

    def test_month_period(self, status_world):
        owner1 = status_world['owners'][0]

        response = get_as(owner1, period='2025-11')

        assert response.data['period'] == '2025-11'
        assert (response.data['totals']['bookings'], revenue(response.data['totals'])) == (1, {'USD': '80.00'})
        assert [row['bookings'] for row in response.data['properties']] == [0, 1]

    def test_other_owner_sees_only_their_own_numbers(self, status_world):
        owner2 = status_world['owners'][1]

        response = get_as(owner2)

        assert (response.data['totals']['bookings'], revenue(response.data['totals'])) == \
            (1, {'KZT': '50000.00', 'USD': '999.00'})  # R12: revenue = paid - refunded incl. money kept from the gamma no-show (999 USD) (was KZT only)
        assert sorted(row['name'] for row in response.data['properties']) == ['Delta Hotel', 'Gamma Hotel']

    def test_staff_without_hotels_sees_zeros(self, status_world):
        staff = User.objects.create_user(email='staff@example.com', password='StaffPassword#123', is_staff=True)

        response = get_as(staff)

        assert (response.status_code, response.data['totals']['bookings'], response.data['properties']) == \
            (200, 0, [])

    @pytest.mark.parametrize('params', [{'period': '2026-13'}, {'year': 'x'}])
    def test_invalid_input_is_400(self, status_world, params):
        assert get_as(status_world['owners'][0], **params).status_code == 400

    def test_query_count_is_constant(self, status_world, django_assert_max_num_queries):
        # R12 (was 8): role check, fully refunded ids (scope, period), totals (4), series (4),
        # reconciliation, years, monthly (3), properties, their revenue (2) and booking value = 19
        with django_assert_max_num_queries(19):
            assert get_as(status_world['owners'][0], year=2026).status_code == 200
