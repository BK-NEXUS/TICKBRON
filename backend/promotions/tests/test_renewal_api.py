"""The super admin's Renewals section: ads waiting for the answer "did the hotel pay for the next month?"."""
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from promotions import renewals
from promotions.models import AdRenewal, Promotion
from promotions.tests.helpers import make_guest, make_hotel, make_owner, make_staff, make_superadmin
from promotions.tests.test_renewals import END, ad

pytestmark = pytest.mark.django_db

LIST = '/api/v1/admin-panel/promotions/renewals/'


def client_of(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.fixture
def boss():
    return client_of(make_superadmin())


@pytest.fixture
def waiting():
    """Two ads whose renewal is open: one ends today, one ended three days ago."""
    first = ad(end=END, hotel=make_hotel(make_owner('a@example.com'), name='Alpha'))
    second = ad(end=END - timedelta(days=3), hotel=make_hotel(make_owner('b@example.com'), name='Beta'))
    renewals.open_due(today=END)
    return first, second


def url(renewal, action):
    return f'{LIST}{renewal.id}/{action}/'


class TestTheList:
    def test_waiting_ads_come_nearest_deadline_first_with_what_the_panel_needs(self, boss, waiting, monkeypatch):
        monkeypatch.setattr('promotions.renewal_views.business_today', lambda: END)
        response = boss.get(LIST)
        assert response.status_code == 200, response.data
        assert [row['hotel_name'] for row in response.data['results']] == ['Beta', 'Alpha']
        beta = response.data['results'][0]
        assert (beta['status'], beta['ends_on'], beta['deadline'], beta['days_left']) == (
            'pending', '2026-11-27', '2026-12-02', 2)
        assert (beta['promotion_id'], beta['property_id'], beta['price_amount'], beta['price_currency']) == (
            waiting[1].id, waiting[1].property_id, '1000000.00', 'UZS')
        assert (beta['owner_email'], beta['city'], beta['latitude'], beta['longitude']) == (
            'b@example.com', 'Samarkand', None, None)

    def test_history_by_status_and_a_wrong_status(self, boss, waiting):
        renewals.decline(AdRenewal.objects.get(promotion=waiting[0]), actor=make_superadmin('c@example.com'))
        assert [row['status'] for row in boss.get(LIST, {'status': 'declined'}).data['results']] == ['declined']
        assert len(boss.get(LIST).data['results']) == 1
        assert boss.get(LIST, {'status': 'later'}).status_code == 400

    def test_staff_may_look_but_a_guest_an_owner_and_a_visitor_may_not(self, waiting):
        assert client_of(make_staff()).get(LIST).status_code == 200
        assert client_of(make_guest()).get(LIST).status_code == 403
        assert client_of(make_owner('x@example.com')).get(LIST).status_code == 403
        assert APIClient().get(LIST).status_code in (401, 403)


class TestConfirmAndDecline:
    def test_confirm_extends_the_ad_and_returns_the_row(self, boss, waiting):
        renewal = AdRenewal.objects.get(promotion=waiting[0])
        response = boss.post(url(renewal, 'confirm'), {}, format='json')
        assert response.status_code == 200, response.data
        assert response.data['status'] == 'renewed' and response.data['ends_on'] == '2026-11-30'
        assert Promotion.objects.get(pk=waiting[0].pk).end_date == date(2026, 12, 31)

    def test_decline_removes_the_ad(self, boss, waiting):
        renewal = AdRenewal.objects.get(promotion=waiting[0])
        response = boss.post(url(renewal, 'decline'), {}, format='json')
        assert response.status_code == 200 and response.data['status'] == 'declined'
        assert Promotion.objects.get(pk=waiting[0].pk).status == 'cancelled'

    def test_a_second_answer_is_a_409(self, boss, waiting):
        renewal = AdRenewal.objects.get(promotion=waiting[0])
        boss.post(url(renewal, 'confirm'), {}, format='json')
        assert boss.post(url(renewal, 'confirm'), {}, format='json').status_code == 409
        assert boss.post(url(renewal, 'decline'), {}, format='json').status_code == 409

    def test_an_overlapping_extension_is_a_409_and_changes_nothing(self, boss, waiting):
        Promotion.objects.create(
            property=waiting[0].property, start_date=END + timedelta(days=2), end_date=END + timedelta(days=20),
            status='scheduled')
        renewal = AdRenewal.objects.get(promotion=waiting[0])
        response = boss.post(url(renewal, 'confirm'), {}, format='json')
        assert response.status_code == 409 and response.data['code'] == 'overlap'
        assert AdRenewal.objects.get(pk=renewal.pk).status == 'pending'

    def test_an_unknown_renewal_is_a_404(self, boss):
        assert boss.post(f'{LIST}999999/confirm/', {}, format='json').status_code == 404

    @pytest.mark.parametrize('make_user', [make_staff, make_guest])
    def test_staff_and_others_cannot_answer(self, waiting, make_user):
        renewal = AdRenewal.objects.get(promotion=waiting[0])
        api = client_of(make_user())
        assert api.post(url(renewal, 'confirm'), {}, format='json').status_code == 403
        assert api.post(url(renewal, 'decline'), {}, format='json').status_code == 403
        assert AdRenewal.objects.get(pk=renewal.pk).status == 'pending'

    def test_the_answers_are_in_the_access_log(self, boss, waiting):
        boss.post(url(AdRenewal.objects.get(promotion=waiting[0]), 'confirm'), {}, format='json')
        boss.post(url(AdRenewal.objects.get(promotion=waiting[1]), 'decline'), {}, format='json')
        assert sorted(AdminAccessLog.objects.filter(action__startswith='ad_renewal').values_list('action', flat=True)) == [
            'ad_renewal_confirm', 'ad_renewal_decline']


def test_a_route_exists_for_the_daily_task_at_0005_tashkent():
    from django.conf import settings
    entry = settings.CELERY_BEAT_SCHEDULE['run-ad-renewals']
    assert entry['task'] == 'promotions.tasks.run_ad_renewals'
    assert (entry['schedule'].hour, entry['schedule'].minute) == ({0}, {5})
