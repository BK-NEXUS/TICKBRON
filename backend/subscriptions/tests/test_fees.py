"""The monthly hotel fee: free period, one fee per hotel and month, reminders, payment (plan .ai/PLAN_SUBSCRIPTION.md)."""
from datetime import date
from unittest import mock

import pytest

from accounts.models import Notification
from subscriptions import services
from subscriptions.models import FeeSettings, HotelFeeAccount, MonthlyFee
from subscriptions.tests.helpers import make_hotel
from users.models import User

pytestmark = pytest.mark.django_db

AMOUNT = 300000


@pytest.fixture
def amount():
    settings = FeeSettings.load()
    settings.monthly_amount = AMOUNT
    settings.save()
    return AMOUNT


def codes(user):
    return list(Notification.objects.filter(user=user).order_by('id').values_list('code', flat=True))


class TestFreePeriod:
    def test_the_free_period_is_thirty_days_from_the_first_day_as_an_active_hotel(self):
        hotel = make_hotel()
        account = services.ensure_account(hotel, today=date(2026, 10, 15))
        assert account.free_until == date(2026, 11, 14)

    def test_asking_again_does_not_move_the_end_of_the_free_period(self):
        hotel = make_hotel()
        services.ensure_account(hotel, today=date(2026, 10, 15))
        again = services.ensure_account(hotel, today=date(2026, 12, 1))
        assert again.free_until == date(2026, 11, 14)
        assert HotelFeeAccount.objects.count() == 1


class TestCreatingFees:
    def test_no_fee_while_the_first_of_the_month_is_inside_the_free_period(self, amount):
        hotel = make_hotel()
        services.ensure_account(hotel, today=date(2026, 10, 15))
        assert services.create_due_fees(today=date(2026, 11, 1)) == 0
        assert MonthlyFee.objects.count() == 0

    def test_the_first_fee_is_due_on_the_first_after_the_free_period(self, amount):
        hotel = make_hotel()
        services.ensure_account(hotel, today=date(2026, 10, 15))
        assert services.create_due_fees(today=date(2026, 12, 1)) == 1
        fee = MonthlyFee.objects.get()
        assert (fee.property_id, fee.month, fee.amount, fee.status) == (hotel.id, date(2026, 12, 1), AMOUNT, 'due')

    def test_running_again_creates_nothing_twice(self, amount):
        services.ensure_account(make_hotel(), today=date(2026, 10, 15))
        services.create_due_fees(today=date(2026, 12, 1))
        assert services.create_due_fees(today=date(2026, 12, 1)) == 0
        assert services.create_due_fees(today=date(2026, 12, 9)) == 0
        assert MonthlyFee.objects.count() == 1

    def test_a_day_missed_is_made_up_the_next_day(self, amount):
        services.ensure_account(make_hotel(), today=date(2026, 10, 15))
        assert services.create_due_fees(today=date(2026, 12, 2)) == 1
        assert MonthlyFee.objects.get().month == date(2026, 12, 1)

    def test_nothing_is_billed_until_the_super_admin_sets_an_amount(self):
        services.ensure_account(make_hotel(), today=date(2026, 10, 15))
        assert services.create_due_fees(today=date(2026, 12, 1)) == 0

    @pytest.mark.parametrize('state', ['draft', 'pending_approval', 'suspended', 'rejected'])
    def test_only_active_hotels_are_billed(self, amount, state):
        services.ensure_account(make_hotel(status=state), today=date(2026, 10, 15))
        assert services.create_due_fees(today=date(2026, 12, 1)) == 0

    def test_a_deleted_hotel_is_not_billed(self, amount):
        hotel = make_hotel()
        services.ensure_account(hotel, today=date(2026, 10, 15))
        hotel.soft_delete()
        assert services.create_due_fees(today=date(2026, 12, 1)) == 0

    def test_a_fee_keeps_the_amount_it_was_created_with(self, amount):
        services.ensure_account(make_hotel(), today=date(2026, 10, 15))
        services.create_due_fees(today=date(2026, 12, 1))
        services.set_monthly_amount(450000)
        assert MonthlyFee.objects.get().amount == AMOUNT


class TestDailyRun:
    def test_hotels_that_were_active_before_the_feature_get_thirty_free_days(self, amount):
        hotel = make_hotel()
        services.run_daily(today=date(2026, 12, 1))
        assert HotelFeeAccount.objects.get(property=hotel).free_until == date(2026, 12, 31)
        assert MonthlyFee.objects.count() == 0

    def test_it_creates_the_fee_and_tells_the_owner(self, amount):
        hotel = make_hotel()
        services.ensure_account(hotel, today=date(2026, 10, 15))
        result = services.run_daily(today=date(2026, 12, 1))
        assert result == {'accounts': 0, 'fees': 1, 'notices': 1}
        assert codes(hotel.owner) == ['fee_due']


class TestReminders:
    def make_fee(self, amount):
        hotel = make_hotel()
        services.ensure_account(hotel, today=date(2026, 10, 15))
        services.create_due_fees(today=date(2026, 12, 1))
        return hotel, MonthlyFee.objects.get()

    def test_one_reminder_on_the_due_day_and_not_twice(self, amount):
        hotel, _ = self.make_fee(amount)
        assert services.send_reminders(today=date(2026, 12, 1)) == 1
        assert services.send_reminders(today=date(2026, 12, 1)) == 0
        assert codes(hotel.owner) == ['fee_due']

    def test_the_three_reminders_come_on_day_0_3_and_5(self, amount):
        hotel, _ = self.make_fee(amount)
        for day in (1, 2, 3, 4, 5, 6, 7, 20):
            services.send_reminders(today=date(2026, 12, day))
        assert codes(hotel.owner) == ['fee_due', 'fee_overdue', 'fee_last_warning']

    def test_after_a_long_gap_only_the_latest_reminder_is_sent(self, amount):
        hotel, _ = self.make_fee(amount)
        services.send_reminders(today=date(2026, 12, 8))
        assert codes(hotel.owner) == ['fee_last_warning']

    def test_the_notice_carries_ids_the_amount_and_the_due_date_only(self, amount):
        hotel, fee = self.make_fee(amount)
        services.send_reminders(today=date(2026, 12, 1))
        notice = Notification.objects.get()
        assert notice.params == {'fee_id': fee.id, 'property_id': hotel.id, 'amount': str(AMOUNT),
                                 'currency': 'UZS', 'due_date': '2026-12-01'}

    def test_a_paid_fee_gets_no_reminder(self, amount):
        hotel, fee = self.make_fee(amount)
        services.confirm_paid(fee, actor=User.objects.create_user(email='b@example.com', password='x'))
        Notification.objects.all().delete()
        assert services.send_reminders(today=date(2026, 12, 6)) == 0

    def test_a_failing_notice_is_retried_the_next_day_and_never_raises(self, amount):
        hotel, fee = self.make_fee(amount)
        with mock.patch('subscriptions.services.notify', side_effect=RuntimeError('boom')):
            assert services.send_reminders(today=date(2026, 12, 1)) == 0
        fee.refresh_from_db()
        assert fee.reminder_stage == 0
        assert services.send_reminders(today=date(2026, 12, 2)) == 1
        assert codes(hotel.owner) == ['fee_due']


class TestPhase:
    @pytest.mark.parametrize('day, phase', [(1, 'due'), (6, 'due'), (7, 'late'), (30, 'late')])
    def test_waiting_time_is_five_days_after_the_due_date(self, amount, day, phase):
        services.ensure_account(make_hotel(), today=date(2026, 10, 15))
        services.create_due_fees(today=date(2026, 12, 1))
        assert services.phase(MonthlyFee.objects.get(), today=date(2026, 12, day)) == phase

    def test_a_paid_fee_is_paid(self, amount):
        services.ensure_account(make_hotel(), today=date(2026, 10, 15))
        services.create_due_fees(today=date(2026, 12, 1))
        fee = services.confirm_paid(
            MonthlyFee.objects.get(), actor=User.objects.create_user(email='b@example.com', password='x'))
        assert services.phase(fee, today=date(2026, 12, 30)) == 'paid'


class TestPayment:
    @pytest.fixture
    def fee(self, amount):
        hotel = make_hotel()
        services.ensure_account(hotel, today=date(2026, 10, 15))
        services.create_due_fees(today=date(2026, 12, 1))
        return MonthlyFee.objects.get()

    @pytest.fixture
    def boss(self):
        return User.objects.create_user(email='boss@example.com', password='x', is_staff=True, is_superuser=True)

    def test_confirming_records_who_when_and_how_and_tells_the_owner(self, fee, boss):
        services.confirm_paid(fee, actor=boss, note='cash, receipt 12')
        fee.refresh_from_db()
        assert (fee.status, fee.confirmed_by_id, fee.confirmed_via, fee.note) == ('paid', boss.id, 'panel', 'cash, receipt 12')
        assert fee.paid_at is not None
        assert codes(fee.property.owner) == ['fee_paid']

    def test_confirming_twice_is_refused(self, fee, boss):
        services.confirm_paid(fee, actor=boss)
        with pytest.raises(services.FeeStateError):
            services.confirm_paid(fee, actor=boss)

    def test_undo_makes_it_due_again_and_clears_the_confirmation(self, fee, boss):
        services.confirm_paid(fee, actor=boss, note='x')
        services.undo_paid(fee)
        fee.refresh_from_db()
        assert (fee.status, fee.paid_at, fee.confirmed_by, fee.confirmed_via, fee.note) == ('due', None, None, '', '')

    def test_undo_of_an_unpaid_fee_is_refused(self, fee, boss):
        with pytest.raises(services.FeeStateError):
            services.undo_paid(fee)

    def test_a_failing_notice_does_not_stop_the_confirmation(self, fee, boss):
        with mock.patch('subscriptions.services.notify', side_effect=RuntimeError('boom')):
            services.confirm_paid(fee, actor=boss)
        fee.refresh_from_db()
        assert fee.status == 'paid'


class TestAmountSetting:
    def test_the_amount_starts_unset_and_can_be_changed(self):
        assert FeeSettings.load().monthly_amount == 0
        services.set_monthly_amount(250000)
        assert FeeSettings.load().monthly_amount == 250000
