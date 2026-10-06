"""
R12 phase 3: access matrix for every new endpoint (anonymous, guest, owner, staff, super-admin)
and constant query counts for the lists.
"""
from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from bookings.models import NoShowReport
from bookings.tests.r12b_helpers import A, COMMENT, P, client_for, make_stay, past_stay, report_url, world  # noqa: F401

OWNER_ENDPOINTS = [
    ('post', f'{P}/bookings/1/no-show-report/'),
    ('get', f'{P}/no-show-reports/'),
    ('post', f'{P}/no-show-reports/1/withdraw/'),
]
STAFF_ENDPOINTS = [
    ('get', f'{A}/no-show-reports/'),
    ('get', f'{A}/no-show-reports/1/'),
    ('post', f'{A}/no-show-reports/1/approve/'),
    ('post', f'{A}/no-show-reports/1/reject/'),
    ('post', f'{A}/no-show-reports/1/reverse/'),
]


def call(user, method, url):
    return getattr(client_for(user), method)(url, {}, format='json')


@pytest.mark.django_db
class TestAccessMatrix:

    @pytest.mark.parametrize('method,url', OWNER_ENDPOINTS + STAFF_ENDPOINTS)
    def test_anonymous_is_rejected(self, method, url):
        assert call(None, method, url).status_code in (401, 403)

    @pytest.mark.parametrize('method,url', OWNER_ENDPOINTS + STAFF_ENDPOINTS)
    def test_guest_gets_403(self, world, method, url):
        assert call(world['guest'], method, url).status_code == 403

    @pytest.mark.parametrize('method,url', STAFF_ENDPOINTS)
    def test_hotel_owner_cannot_use_staff_endpoints(self, world, method, url):
        assert call(world['owner'], method, url).status_code == 403

    @pytest.mark.parametrize('method,url', OWNER_ENDPOINTS)
    def test_hotel_owner_is_let_through_to_their_own_data(self, world, method, url):
        # 400/404 are fine (empty body, ids that do not exist); only 401/403 are not
        assert call(world['owner'], method, url).status_code not in (401, 403)

    @pytest.mark.parametrize('method,url', STAFF_ENDPOINTS)
    def test_staff_and_super_admin_are_let_through(self, world, method, url):
        assert call(world['staff'], method, url).status_code not in (401, 403)
        assert call(world['super'], method, url).status_code not in (401, 403)

    @pytest.mark.parametrize('method,url', OWNER_ENDPOINTS)
    def test_staff_only_see_hotels_they_own(self, world, method, url):
        response = call(world['staff'], method, url)
        assert response.status_code not in (401, 403)

    def test_owner_cannot_see_or_touch_another_owners_reports(self, world):
        other = make_stay(world['other_prop'], world['guest'], world['today'] - timedelta(days=3),
                          room=world['other_room'], rate=world['other_rate'])
        report_id = client_for(world['other_owner']).post(
            report_url(other), {'comment': COMMENT}, format='json').data['id']
        owner = client_for(world['owner'])
        assert owner.get(f'{P}/no-show-reports/').data['results'] == []
        assert owner.post(f'{P}/no-show-reports/{report_id}/withdraw/').status_code == 404
        assert NoShowReport.objects.get().status == 'pending'


@pytest.mark.django_db
class TestConstantQueries:

    def _count(self, client, url):
        client.get(url)                                    # warm caches (content types, permissions)
        with CaptureQueriesContext(connection) as queries:
            response = client.get(url)
        assert response.status_code == 200
        return len(queries)

    def _add_reports(self, world, count):
        for _ in range(count):
            booking = past_stay(world)
            client_for(world['owner']).post(report_url(booking), {'comment': COMMENT}, format='json')

    @pytest.mark.parametrize('who,url', [
        ('staff', f'{A}/no-show-reports/'),
        ('owner', f'{P}/no-show-reports/'),
    ])
    def test_list_query_count_does_not_grow_with_the_data(self, world, who, url):
        self._add_reports(world, 3)
        small = self._count(client_for(world[who]), url)
        self._add_reports(world, 27)
        large = self._count(client_for(world[who]), url)
        assert small == large

    def test_detail_query_count_is_small(self, world):
        self._add_reports(world, 5)
        report_id = NoShowReport.objects.first().pk
        assert self._count(client_for(world['staff']), f'{A}/no-show-reports/{report_id}/') <= 14
