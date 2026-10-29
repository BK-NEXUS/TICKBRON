"""The super admin's Payments tab: list a month, mark a fee paid or undo it, the amount (plan .ai/PLAN_SUBSCRIPTION.md)."""
from datetime import date

import pytest
from rest_framework.test import APIClient

from accounts.models import Notification
from admin_panel.models import AdminAccessLog
from admin_panel.tests.listing_helpers import make_listable
from common.dates import business_today
from subscriptions import services
from subscriptions.models import HotelFeeAccount, MonthlyFee
from subscriptions.tests.helpers import make_hotel
from users.models import User

pytestmark = pytest.mark.django_db

LIST = '/api/v1/admin-panel/fees/'
SETTINGS = '/api/v1/admin-panel/fees/settings/'
DEC = date(2026, 12, 1)


def client_of(**flags):
    user = User.objects.create_user(email=f'u{User.objects.count()}@example.com', password='x', **flags)
    api = APIClient()
    api.force_authenticate(user=user)
    return api, user


@pytest.fixture
def boss():
    return client_of(is_staff=True, is_superuser=True)


@pytest.fixture
def billed():
    """Four active hotels in December 2026: one late, one on time, one paid, one still free."""
    services.set_monthly_amount(300000)
    hotels = {name: make_hotel(name=name, city=city) for name, city in (
        ('Late Hotel', 'Tashkent'), ('Fresh Hotel', 'Samarkand'), ('Paid Hotel', 'Bukhara'), ('Free Hotel', 'Khiva'))}
    for name, hotel in hotels.items():
        services.ensure_account(hotel, today=date(2026, 12, 20) if name == 'Free Hotel' else date(2026, 10, 15))
    services.create_due_fees(today=DEC)
    paid = MonthlyFee.objects.get(property=hotels['Paid Hotel'])
    services.confirm_paid(paid, actor=User.objects.create_user(email='c@example.com', password='x'))
    return hotels


def rows_by_name(response):
    return {row['name']: row for row in response.data['results']}


class TestTheList:
    def test_a_month_lists_each_hotel_with_its_state(self, boss, billed, monkeypatch):
        monkeypatch.setattr('subscriptions.admin_views.business_today', lambda: date(2026, 12, 9))
        response = boss[0].get(LIST, {'month': '2026-12'})
        assert response.status_code == 200
        rows = rows_by_name(response)
        assert {name: row['phase'] for name, row in rows.items()} == {
            'Late Hotel': 'late', 'Fresh Hotel': 'late', 'Paid Hotel': 'paid', 'Free Hotel': 'free'}
        assert response.data['summary'] == {'free': 1, 'due': 0, 'late': 2, 'paid': 1,
                                            'collected': 300000, 'outstanding': 600000}
        assert (response.data['month'], response.data['monthly_amount']) == ('2026-12', 300000)

    def test_a_row_has_what_the_panel_and_the_map_need(self, boss, billed, monkeypatch):
        monkeypatch.setattr('subscriptions.admin_views.business_today', lambda: date(2026, 12, 3))
        row = rows_by_name(boss[0].get(LIST, {'month': '2026-12'}))['Fresh Hotel']
        assert row['phase'] == 'due' and row['days_late'] == 2 and row['due_date'] == '2026-12-01'
        assert (row['city'], row['amount'], row['fee_id']) == ('Samarkand', 300000, MonthlyFee.objects.get(
            property=billed['Fresh Hotel']).id)
        assert (row['latitude'], row['longitude']) == ('41.311081', '69.240562')
        assert (row['owner_name'], row['owner_phone']) == ('Olim Egasi', '+998901112233')
        assert row['owner_email'].endswith('@example.com')

    def test_the_month_defaults_to_this_month(self, boss, billed):
        response = boss[0].get(LIST)
        assert response.data['month'] == business_today().strftime('%Y-%m')

    def test_filter_by_state_and_search_by_name_or_city(self, boss, billed, monkeypatch):
        monkeypatch.setattr('subscriptions.admin_views.business_today', lambda: date(2026, 12, 9))
        api = boss[0]
        assert set(rows_by_name(api.get(LIST, {'month': '2026-12', 'status': 'paid'}))) == {'Paid Hotel'}
        assert set(rows_by_name(api.get(LIST, {'month': '2026-12', 'search': 'kand'}))) == {'Fresh Hotel'}
        assert set(rows_by_name(api.get(LIST, {'month': '2026-12', 'search': 'late'}))) == {'Late Hotel'}

    def test_the_late_hotels_come_first(self, boss, billed, monkeypatch):
        monkeypatch.setattr('subscriptions.admin_views.business_today', lambda: date(2026, 12, 9))
        phases = [row['phase'] for row in boss[0].get(LIST, {'month': '2026-12'}).data['results']]
        assert phases == ['late', 'late', 'paid', 'free']

    def test_an_unset_amount_shows_active_hotels_as_not_billed(self, boss):
        hotel = make_hotel()
        services.ensure_account(hotel, today=date(2026, 6, 1))
        row = rows_by_name(boss[0].get(LIST, {'month': '2026-12'}))['Kolya Hotel']
        assert (row['phase'], row['fee_id'], row['amount']) == ('not_billed', None, None)

    def test_a_hidden_hotel_with_a_fee_stays_in_the_list(self, boss, billed):
        billed['Late Hotel'].status = 'suspended'
        billed['Late Hotel'].save()
        assert 'Late Hotel' in rows_by_name(boss[0].get(LIST, {'month': '2026-12'}))

    @pytest.mark.parametrize('query', [{'month': '2026-13'}, {'month': 'december'}, {'month': '2026-12-01'},
                                       {'status': 'cancelled'}])
    def test_a_wrong_month_or_state_is_a_400(self, boss, query):
        assert boss[0].get(LIST, query).status_code == 400

    def test_staff_may_look_but_a_guest_and_an_owner_may_not(self, billed):
        assert client_of(is_staff=True)[0].get(LIST).status_code == 200
        assert client_of()[0].get(LIST).status_code == 403
        assert APIClient().get(LIST).status_code in (401, 403)


class TestMarkPaid:
    def url(self, hotel, what='mark-paid'):
        return f'/api/v1/admin-panel/fees/{MonthlyFee.objects.get(property=hotel).id}/{what}/'

    def test_the_super_admin_marks_a_fee_paid_with_a_note(self, boss, billed):
        response = boss[0].post(self.url(billed['Late Hotel']), {'note': 'cash, receipt 7'}, format='json')
        assert response.status_code == 200, response.data
        assert response.data['status'] == 'paid'
        fee = MonthlyFee.objects.get(property=billed['Late Hotel'])
        assert (fee.status, fee.confirmed_by_id, fee.confirmed_via, fee.note) == ('paid', boss[1].id, 'panel', 'cash, receipt 7')
        assert Notification.objects.filter(user=billed['Late Hotel'].owner, code='fee_paid').count() == 1

    def test_it_is_written_to_the_access_log(self, boss, billed):
        boss[0].post(self.url(billed['Late Hotel']), {}, format='json')
        row = AdminAccessLog.objects.get(action='fee_mark_paid')
        fee = MonthlyFee.objects.get(property=billed['Late Hotel'])
        assert (row.actor_id, row.details) == (boss[1].id, {'object_id': fee.id, 'property_id': billed['Late Hotel'].id})

    def test_marking_twice_is_a_409(self, boss, billed):
        boss[0].post(self.url(billed['Late Hotel']), {}, format='json')
        assert boss[0].post(self.url(billed['Late Hotel']), {}, format='json').status_code == 409

    def test_undo_brings_it_back_to_due(self, boss, billed):
        response = boss[0].post(self.url(billed['Paid Hotel'], 'undo'), {}, format='json')
        assert response.status_code == 200 and response.data['status'] == 'due'
        assert AdminAccessLog.objects.filter(action='fee_undo_paid').count() == 1

    def test_undo_of_an_unpaid_fee_is_a_409(self, boss, billed):
        assert boss[0].post(self.url(billed['Late Hotel'], 'undo'), {}, format='json').status_code == 409

    def test_an_unknown_fee_is_a_404(self, boss):
        assert boss[0].post('/api/v1/admin-panel/fees/999999/mark-paid/', {}, format='json').status_code == 404

    def test_a_long_note_is_a_400(self, boss, billed):
        assert boss[0].post(self.url(billed['Late Hotel']), {'note': 'x' * 201}, format='json').status_code == 400

    @pytest.mark.parametrize('flags', [{'is_staff': True}, {}])
    def test_staff_and_others_cannot_mark_or_undo(self, billed, flags):
        api, _ = client_of(**flags)
        assert api.post(self.url(billed['Late Hotel']), {}, format='json').status_code == 403
        assert api.post(self.url(billed['Paid Hotel'], 'undo'), {}, format='json').status_code == 403
        assert MonthlyFee.objects.get(property=billed['Late Hotel']).status == 'due'


class TestAmountSetting:
    def test_the_super_admin_reads_and_changes_the_amount(self, boss):
        assert boss[0].get(SETTINGS).data == {'monthly_amount': 0, 'currency': 'UZS'}
        response = boss[0].put(SETTINGS, {'monthly_amount': 350000}, format='json')
        assert response.status_code == 200 and response.data['monthly_amount'] == 350000
        row = AdminAccessLog.objects.get(action='fee_amount_update')
        assert row.details == {'amount': 350000}

    @pytest.mark.parametrize('value', [-1, 'many', 1.5, 2_000_000_001, None, ''])
    def test_a_bad_amount_is_a_400(self, boss, value):
        assert boss[0].put(SETTINGS, {'monthly_amount': value}, format='json').status_code == 400

    @pytest.mark.parametrize('flags', [{'is_staff': True}, {}])
    def test_staff_and_others_cannot_read_or_change_it(self, flags):
        api, _ = client_of(**flags)
        assert api.get(SETTINGS).status_code == 403
        assert api.put(SETTINGS, {'monthly_amount': 1}, format='json').status_code == 403


class TestApprovingAHotelStartsTheFreePeriod:
    def test_the_account_is_created_when_the_hotel_is_approved(self, boss):
        hotel = make_hotel(status='pending_approval')
        make_listable(hotel)
        response = boss[0].post(f'/api/v1/admin-panel/properties/{hotel.id}/approve/', {}, format='json')
        assert response.status_code == 200, response.data
        assert HotelFeeAccount.objects.get(property=hotel).free_until == business_today() + services.FREE_PERIOD

    def test_a_rejected_hotel_gets_no_account(self, boss):
        hotel = make_hotel(status='pending_approval')
        boss[0].post(f'/api/v1/admin-panel/properties/{hotel.id}/approve/', {'rejection_reason': 'No photos'},
                     format='json')
        assert not HotelFeeAccount.objects.filter(property=hotel).exists()
