"""The commission the site takes from each hotel owner: a percent per owner, figures per month and per year,
and the confirmation that a month was paid (by a super admin or a staff admin, shown by name)."""
from datetime import date, datetime, timezone
from unittest import mock

import pytest
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from admin_panel.tests.status_fixtures import make_booking
from partner.models import CommissionPayment, CommissionRate
from partner.tests.geography_helpers import uzbek_location
from promotions.tests.helpers import make_guest, make_hotel, make_owner, make_staff, make_superadmin
from users.models import User

pytestmark = pytest.mark.django_db

TODAY = date(2026, 5, 15)
OWNER_URL = '/api/v1/partner/commission/'
LIST_URL = '/api/v1/admin-panel/commission/'
CREATE_OWNER = '/api/v1/admin-panel/users/create-hotel-owner/'


def detail(owner):
    return f'/api/v1/admin-panel/commission/{owner.id}/'


def rate_url(owner):
    return f'/api/v1/admin-panel/commission/{owner.id}/rate/'


def paid_url(owner, month):
    return f'/api/v1/admin-panel/commission/{owner.id}/months/{month}/paid/'


def client_of(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.fixture(autouse=True)
def frozen_today():
    with mock.patch('partner.commission.business_today', return_value=TODAY):
        yield


@pytest.fixture
def owner():
    return make_owner('mine@example.com')


@pytest.fixture
def hotel(owner):
    return make_hotel(owner, name='My Hotel')


@pytest.fixture
def guest():
    return make_guest('traveller@example.com')


def set_rate(owner, percent, since=date(2026, 1, 1)):
    return CommissionRate.objects.create(owner=owner, percent=percent, effective_from=since)


def month_of(response, month):
    return next(row for row in response.data['months'] if row['month'] == month)


class TestFigures:
    def test_only_confirmed_and_completed_bookings_count(self, owner, hotel, guest):
        set_rate(owner, '2.00')
        make_booking(guest, hotel, date(2026, 3, 5), '1000.00', status='confirmed', currency='USD')
        make_booking(guest, hotel, date(2026, 3, 9), '500.00', status='completed', currency='USD')
        for state in ('pending', 'cancelled', 'no_show'):
            make_booking(guest, hotel, date(2026, 3, 12), '999.00', status=state, currency='USD')

        march = month_of(client_of(owner).get(OWNER_URL), '2026-03')

        assert march['bookings'] == 2
        assert march['gross'] == [{'currency': 'USD', 'amount': '1500.00'}]
        assert march['commission'] == [{'currency': 'USD', 'amount': '30.00'}]
        assert march['percent'] == '2.00'

    def test_each_month_and_each_currency_is_counted_apart(self, owner, hotel, guest):
        set_rate(owner, '10.00')
        make_booking(guest, hotel, date(2026, 3, 5), '100.00', currency='USD')
        make_booking(guest, hotel, date(2026, 3, 6), '1000000.00', currency='UZS')
        make_booking(guest, hotel, date(2026, 4, 6), '200.00', currency='USD')

        response = client_of(owner).get(OWNER_URL)

        assert month_of(response, '2026-03')['commission'] == [
            {'currency': 'USD', 'amount': '10.00'}, {'currency': 'UZS', 'amount': '100000.00'}]
        assert month_of(response, '2026-04')['commission'] == [{'currency': 'USD', 'amount': '20.00'}]

    def test_the_month_is_the_check_in_month(self, owner, hotel, guest):
        set_rate(owner, '2.00')
        make_booking(guest, hotel, date(2026, 3, 31), '100.00', currency='USD', nights=3)

        months = [row['month'] for row in client_of(owner).get(OWNER_URL).data['months']]

        assert '2026-03' in months and '2026-04' not in months

    def test_the_commission_is_rounded_to_cents(self, owner, hotel, guest):
        set_rate(owner, '2.50')
        make_booking(guest, hotel, date(2026, 3, 5), '33.33', currency='USD')

        assert month_of(client_of(owner).get(OWNER_URL), '2026-03')['commission'] == [{'currency': 'USD', 'amount': '0.83'}]

    def test_the_current_month_is_always_listed_even_without_bookings(self, owner):
        response = client_of(owner).get(OWNER_URL)

        assert [row['month'] for row in response.data['months']] == ['2026-05']
        assert month_of(response, '2026-05')['bookings'] == 0

    def test_months_come_newest_first(self, owner, hotel, guest):
        make_booking(guest, hotel, date(2026, 1, 5), '1.00', currency='USD')
        make_booking(guest, hotel, date(2026, 3, 5), '1.00', currency='USD')

        months = [row['month'] for row in client_of(owner).get(OWNER_URL).data['months']]

        assert months == sorted(months, reverse=True)

    def test_the_other_owners_bookings_are_not_mine(self, owner, hotel, guest):
        other_hotel = make_hotel(make_owner('other@example.com'), name='Other')
        make_booking(guest, other_hotel, date(2026, 3, 5), '5000.00', currency='USD')

        assert 'USD' not in str(client_of(owner).get(OWNER_URL).data['months'])


class TestPercentHistory:
    def test_without_a_percent_there_is_no_commission(self, owner, hotel, guest):
        make_booking(guest, hotel, date(2026, 3, 5), '100.00', currency='USD')

        response = client_of(owner).get(OWNER_URL)

        assert response.data['percent'] is None
        march = month_of(response, '2026-03')
        assert (march['percent'], march['commission']) == (None, None)
        assert march['gross'] == [{'currency': 'USD', 'amount': '100.00'}]

    def test_a_percent_applies_from_the_month_it_was_set_not_to_earlier_months(self, owner, hotel, guest):
        set_rate(owner, '2.00', since=date(2026, 4, 1))
        make_booking(guest, hotel, date(2026, 3, 5), '100.00', currency='USD')
        make_booking(guest, hotel, date(2026, 4, 5), '100.00', currency='USD')

        response = client_of(owner).get(OWNER_URL)

        assert month_of(response, '2026-03')['commission'] is None
        assert month_of(response, '2026-04')['commission'] == [{'currency': 'USD', 'amount': '2.00'}]
        assert response.data['percent'] == '2.00'

    def test_a_later_change_keeps_the_old_percent_for_the_old_months(self, owner, hotel, guest):
        set_rate(owner, '2.00', since=date(2026, 1, 1))
        set_rate(owner, '5.00', since=date(2026, 4, 1))
        make_booking(guest, hotel, date(2026, 3, 5), '100.00', currency='USD')
        make_booking(guest, hotel, date(2026, 4, 5), '100.00', currency='USD')

        response = client_of(owner).get(OWNER_URL)

        assert month_of(response, '2026-03')['percent'] == '2.00'
        assert month_of(response, '2026-04')['percent'] == '5.00'
        assert response.data['percent'] == '5.00'


class TestYears:
    def test_a_young_account_sees_months_only(self, owner, hotel, guest):
        make_booking(guest, hotel, date(2026, 3, 5), '100.00', currency='USD')
        User.objects.filter(pk=owner.pk).update(date_joined=datetime(2026, 1, 1, tzinfo=timezone.utc))
        owner.refresh_from_db()

        assert client_of(owner).get(OWNER_URL).data['years'] is None

    def test_an_account_a_year_old_also_sees_year_totals(self, owner, hotel, guest):
        set_rate(owner, '10.00', since=date(2025, 1, 1))
        User.objects.filter(pk=owner.pk).update(date_joined=datetime(2025, 5, 1, tzinfo=timezone.utc))
        owner.refresh_from_db()
        make_booking(guest, hotel, date(2025, 8, 5), '100.00', currency='USD')
        make_booking(guest, hotel, date(2025, 9, 5), '300.00', currency='USD')
        make_booking(guest, hotel, date(2026, 3, 5), '50.00', currency='USD')

        years = client_of(owner).get(OWNER_URL).data['years']

        assert [row['year'] for row in years] == [2026, 2025]
        assert years[1] == {'year': 2025, 'bookings': 2, 'gross': [{'currency': 'USD', 'amount': '400.00'}],
                            'commission': [{'currency': 'USD', 'amount': '40.00'}]}
        assert years[0]['commission'] == [{'currency': 'USD', 'amount': '5.00'}]


class TestOwnerAccess:
    def test_guest_and_anonymous_are_refused(self, guest):
        assert client_of(guest).get(OWNER_URL).status_code == 403
        assert APIClient().get(OWNER_URL).status_code in (401, 403)

    def test_the_owner_cannot_change_anything(self, owner):
        api = client_of(owner)
        assert api.put(rate_url(owner), {'percent': '0.00'}, format='json').status_code == 403
        assert api.post(paid_url(owner, '2026-03'), {}, format='json').status_code == 403
        assert not CommissionRate.objects.filter(owner=owner).exists()


class TestAdminList:
    @pytest.fixture
    def world(self, owner, hotel, guest):
        set_rate(owner, '2.00')
        make_booking(guest, hotel, date(2026, 5, 3), '1000.00', currency='USD')
        make_booking(guest, hotel, date(2026, 3, 3), '1000.00', currency='USD')
        User.objects.filter(pk=owner.pk).update(
            full_name='Olim Karimov', phone_number='+998901112233')
        return owner

    @pytest.mark.parametrize('actor', [make_superadmin, make_staff])
    def test_super_admin_and_staff_see_every_owner_with_this_month(self, actor, world):
        response = client_of(actor()).get(LIST_URL)

        assert response.status_code == 200
        row = next(item for item in response.data['results'] if item['id'] == world.id)
        assert row['name'] == 'Olim Karimov' and row['email'] == 'mine@example.com'
        assert row['percent'] == '2.00'
        assert row['this_month'] == {'month': '2026-05', 'bookings': 1,
                                     'gross': [{'currency': 'USD', 'amount': '1000.00'}],
                                     'commission': [{'currency': 'USD', 'amount': '20.00'}]}
        assert row['unpaid'] == [{'currency': 'USD', 'amount': '20.00'}]  # March only: May has not ended

    @pytest.mark.parametrize('term', ['Olim', 'karimov', 'mine@example', '901112233', 'My Hotel', 'my hotel'])
    def test_search_finds_the_owner_by_name_email_phone_or_hotel(self, term, world):
        make_owner('stranger@example.com')

        response = client_of(make_staff()).get(LIST_URL, {'search': term})

        assert [item['id'] for item in response.data['results']] == [world.id]

    def test_search_without_a_match_is_an_empty_list(self, world):
        assert client_of(make_staff()).get(LIST_URL, {'search': 'nobody-like-this'}).data['results'] == []

    def test_only_hotel_owners_are_listed(self, world, guest):
        ids = [item['id'] for item in client_of(make_staff()).get(LIST_URL).data['results']]

        assert guest.id not in ids and ids == [world.id]

    def test_an_owner_without_a_percent_is_listed_with_no_percent(self):
        lonely = make_owner('lonely@example.com')

        row = client_of(make_staff()).get(LIST_URL).data['results'][0]

        assert row['id'] == lonely.id and row['percent'] is None and row['this_month']['commission'] is None

    def test_guest_owner_and_anonymous_are_refused(self, owner, guest):
        assert client_of(guest).get(LIST_URL).status_code == 403
        assert client_of(owner).get(LIST_URL).status_code == 403
        assert APIClient().get(LIST_URL).status_code in (401, 403)

    def test_a_hostile_search_is_a_clean_answer(self, world):
        api = client_of(make_staff())
        for term in ('%', '_', "' OR 1=1 --", 'x' * 500):
            assert api.get(LIST_URL, {'search': term}).status_code == 200

    def test_the_detail_has_the_same_shape_as_the_owners_own_view(self, world):
        response = client_of(make_staff()).get(detail(world))

        assert response.status_code == 200
        assert set(response.data) == {'percent', 'percent_since', 'months', 'years'}
        assert month_of(response, '2026-03')['commission'] == [{'currency': 'USD', 'amount': '20.00'}]

    def test_the_detail_of_a_guest_or_unknown_account_is_404(self, guest):
        api = client_of(make_staff())
        assert api.get(detail(guest)).status_code == 404
        assert api.get('/api/v1/admin-panel/commission/999999/').status_code == 404


class TestSettingThePercent:
    def test_super_admin_sets_it_from_the_current_month(self, owner):
        boss = make_superadmin()

        response = client_of(boss).put(rate_url(owner), {'percent': '2.50'}, format='json')

        assert response.status_code == 200, response.data
        rate = CommissionRate.objects.get(owner=owner)
        assert (str(rate.percent), rate.effective_from, rate.set_by_id) == ('2.50', date(2026, 5, 1), boss.id)
        assert response.data['percent'] == '2.50'

    def test_setting_it_again_in_the_same_month_replaces_it(self, owner):
        api = client_of(make_superadmin())
        api.put(rate_url(owner), {'percent': '2.00'}, format='json')
        api.put(rate_url(owner), {'percent': '3.00'}, format='json')

        assert list(CommissionRate.objects.filter(owner=owner).values_list('percent', flat=True)) == [3]

    def test_a_change_never_rewrites_an_earlier_month(self, owner):
        set_rate(owner, '2.00', since=date(2026, 1, 1))
        client_of(make_superadmin()).put(rate_url(owner), {'percent': '5.00'}, format='json')

        assert sorted(CommissionRate.objects.filter(owner=owner).values_list('effective_from', 'percent')) == [
            (date(2026, 1, 1), 2), (date(2026, 5, 1), 5)]

    def test_zero_and_one_hundred_are_allowed(self, owner):
        api = client_of(make_superadmin())
        assert api.put(rate_url(owner), {'percent': '0'}, format='json').status_code == 200
        assert api.put(rate_url(owner), {'percent': '100'}, format='json').status_code == 200

    @pytest.mark.parametrize('bad', ['-1', '100.01', 'abc', '', None, '1.234', 'NaN', 'Infinity', [2], {'a': 1}])
    def test_a_bad_percent_is_refused_with_the_field_named(self, owner, bad):
        response = client_of(make_superadmin()).put(rate_url(owner), {'percent': bad}, format='json')

        assert response.status_code == 400 and 'percent' in response.data
        assert not CommissionRate.objects.filter(owner=owner).exists()

    def test_a_body_that_is_not_an_object_is_a_400(self, owner):
        assert client_of(make_superadmin()).put(rate_url(owner), ['2'], format='json').status_code == 400

    def test_only_a_super_admin_may_set_it(self, owner, guest):
        for actor in (make_staff(), guest):
            assert client_of(actor).put(rate_url(owner), {'percent': '2.00'}, format='json').status_code == 403
        assert APIClient().put(rate_url(owner), {'percent': '2.00'}, format='json').status_code in (401, 403)
        assert not CommissionRate.objects.filter(owner=owner).exists()

    def test_it_can_only_be_set_for_a_hotel_owner(self, guest):
        assert client_of(make_superadmin()).put(rate_url(guest), {'percent': '2.00'}, format='json').status_code == 404

    def test_the_change_is_logged_with_the_percent_and_the_owner(self, owner):
        boss = make_superadmin()
        client_of(boss).put(rate_url(owner), {'percent': '2.50'}, format='json')

        row = AdminAccessLog.objects.get(action='commission_rate_set')
        assert (row.actor_id, row.target_user_id, row.details) == (boss.id, owner.id, {'percent': '2.50'})


class TestCreatingAnOwner:
    BODY = {'email': 'newowner@example.com', 'first_name': 'New', 'last_name': 'Owner', 'phone_number': '+998901234567',
            'password': 'Owner#Secret2026', 'password_confirm': 'Owner#Secret2026'}

    def body(self, **extra):
        return {**self.BODY, **uzbek_location('Tashkent'), **extra}

    def test_the_percent_is_required(self):
        data = self.body()
        del data['commission_percent']

        response = client_of(make_superadmin()).post(CREATE_OWNER, data, format='json')

        assert response.status_code == 400 and 'commission_percent' in response.data
        assert not User.objects.filter(email='newowner@example.com').exists()

    @pytest.mark.parametrize('bad', ['-1', '101', 'abc', '', None])
    def test_a_bad_percent_creates_no_account(self, bad):
        response = client_of(make_superadmin()).post(CREATE_OWNER, self.body(commission_percent=bad), format='json')

        assert response.status_code == 400 and 'commission_percent' in response.data
        assert not User.objects.filter(email='newowner@example.com').exists()

    def test_the_percent_is_stored_from_the_month_of_creation(self):
        response = client_of(make_superadmin()).post(CREATE_OWNER, self.body(commission_percent='3.50'), format='json')

        assert response.status_code == 201, response.data
        rate = CommissionRate.objects.get(owner__email='newowner@example.com')
        assert (str(rate.percent), rate.effective_from) == ('3.50', date(2026, 5, 1))


class TestPaid:
    @pytest.fixture
    def world(self, owner, hotel, guest):
        set_rate(owner, '10.00')
        make_booking(guest, hotel, date(2026, 3, 5), '1000.00', currency='USD')
        return owner

    def test_staff_confirms_a_month_and_the_name_is_recorded(self, world):
        staff = make_staff()
        User.objects.filter(pk=staff.pk).update(full_name=None, first_name='Kola', last_name='Admin')
        staff.refresh_from_db()

        response = client_of(staff).post(paid_url(world, '2026-03'), {}, format='json')

        assert response.status_code == 200, response.data
        paid = month_of(response, '2026-03')['paid']
        assert (paid['by'], paid['role']) == ('Kola Admin', 'staff')
        assert paid['amounts'] == [{'currency': 'USD', 'amount': '100.00'}]
        assert paid['at']

    def test_a_super_admin_is_marked_as_one(self, world):
        boss = make_superadmin()
        User.objects.filter(pk=boss.pk).update(full_name=None, first_name='Boss', last_name='Person')
        boss.refresh_from_db()

        paid = month_of(client_of(boss).post(paid_url(world, '2026-03'), {}, format='json'), '2026-03')['paid']

        assert (paid['by'], paid['role']) == ('Boss Person', 'super_admin')

    def test_the_owner_sees_who_confirmed_it(self, world):
        client_of(make_staff()).post(paid_url(world, '2026-03'), {}, format='json')

        assert month_of(client_of(world).get(OWNER_URL), '2026-03')['paid']['role'] == 'staff'

    def test_a_month_cannot_be_confirmed_twice(self, world):
        api = client_of(make_staff())
        api.post(paid_url(world, '2026-03'), {}, format='json')

        assert api.post(paid_url(world, '2026-03'), {}, format='json').status_code == 409
        assert CommissionPayment.objects.filter(owner=world).count() == 1

    def test_the_confirmed_amount_does_not_move_when_bookings_change_later(self, world, hotel, guest):
        client_of(make_staff()).post(paid_url(world, '2026-03'), {}, format='json')
        make_booking(guest, hotel, date(2026, 3, 20), '1000.00', currency='USD')

        march = month_of(client_of(world).get(OWNER_URL), '2026-03')

        assert march['commission'] == [{'currency': 'USD', 'amount': '200.00'}]
        assert march['paid']['amounts'] == [{'currency': 'USD', 'amount': '100.00'}]

    def test_nothing_to_pay_is_refused(self, owner):
        set_rate(owner, '10.00')

        assert client_of(make_staff()).post(paid_url(owner, '2026-03'), {}, format='json').status_code == 400

    def test_a_month_without_a_percent_is_refused(self, owner, hotel, guest):
        make_booking(guest, hotel, date(2026, 3, 5), '1000.00', currency='USD')

        assert client_of(make_staff()).post(paid_url(owner, '2026-03'), {}, format='json').status_code == 400

    def test_a_month_that_has_not_ended_cannot_be_confirmed(self, world, hotel, guest):
        make_booking(guest, hotel, date(2026, 5, 2), '1000.00', currency='USD')
        make_booking(guest, hotel, date(2026, 7, 2), '1000.00', currency='USD')
        api = client_of(make_staff())

        assert api.post(paid_url(world, '2026-05'), {}, format='json').status_code == 400
        assert api.post(paid_url(world, '2026-07'), {}, format='json').status_code == 400

    @pytest.mark.parametrize('month', ['2026-13', '2026-3', 'march', '2026-03-01', '0000-01'])
    def test_a_bad_month_is_404(self, world, month):
        assert client_of(make_staff()).post(paid_url(world, month), {}, format='json').status_code == 404

    def test_staff_or_super_admin_can_take_the_confirmation_back(self, world):
        api = client_of(make_staff())
        api.post(paid_url(world, '2026-03'), {}, format='json')

        response = client_of(make_superadmin()).delete(paid_url(world, '2026-03'))

        assert response.status_code == 200
        assert month_of(response, '2026-03')['paid'] is None
        assert not CommissionPayment.objects.filter(owner=world).exists()

    def test_taking_back_what_was_never_confirmed_is_404(self, world):
        assert client_of(make_staff()).delete(paid_url(world, '2026-03')).status_code == 404

    def test_guest_owner_and_anonymous_cannot_confirm_or_undo(self, world, guest):
        for actor in (guest, world):
            api = client_of(actor)
            assert api.post(paid_url(world, '2026-03'), {}, format='json').status_code == 403
            assert api.delete(paid_url(world, '2026-03')).status_code == 403
        assert APIClient().post(paid_url(world, '2026-03'), {}, format='json').status_code in (401, 403)
        assert not CommissionPayment.objects.exists()

    def test_both_steps_are_logged(self, world):
        staff = make_staff()
        api = client_of(staff)
        api.post(paid_url(world, '2026-03'), {}, format='json')
        api.delete(paid_url(world, '2026-03'))

        rows = AdminAccessLog.objects.filter(action__in=('commission_paid', 'commission_unpaid')).order_by('id')
        assert [(row.action, row.actor_id, row.target_user_id, row.details) for row in rows] == [
            ('commission_paid', staff.id, world.id, {'month': '2026-03'}),
            ('commission_unpaid', staff.id, world.id, {'month': '2026-03'})]

    def test_the_list_counts_only_unconfirmed_months_as_unpaid(self, world):
        staff = make_staff()
        client_of(staff).post(paid_url(world, '2026-03'), {}, format='json')

        row = client_of(staff).get(LIST_URL).data['results'][0]

        assert row['unpaid'] == []
