"""Monthly ad renewal: asked on the end day, the ad stays visible 5 more days, then it is removed (plan .ai/PLAN_AD_RENEWAL.md)."""
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

import pytest
from django.utils import timezone

from accounts.models import Notification
from admin_panel.models import AdminAccessLog
from promotions import renewals, service
from promotions.models import AdRenewal, Promotion
from promotions.tests.helpers import make_hotel, make_owner, make_superadmin

pytestmark = pytest.mark.django_db

END = date(2026, 11, 30)


def ad(end=END, status='active', paid=True, hotel=None, days=30):
    hotel = hotel or make_hotel(make_owner(f'o{Promotion.objects.count()}@example.com'), name=f'Hotel {Promotion.objects.count()}')
    return Promotion.objects.create(
        property=hotel, start_date=end - timedelta(days=days - 1), end_date=end, status=status,
        price_amount=Decimal('1000000'), price_currency='UZS', paid_at=timezone.now() if paid else None)


def codes(user):
    return list(Notification.objects.filter(user=user).order_by('id').values_list('code', flat=True))


class TestOpening:
    def test_opened_on_the_end_day_with_a_deadline_five_days_later(self):
        promotion = ad()
        assert renewals.open_due(today=END) == 1
        renewal = AdRenewal.objects.get()
        assert (renewal.promotion_id, renewal.ends_on, renewal.deadline, renewal.status) == (
            promotion.id, END, END + timedelta(days=5), 'pending')

    def test_not_before_the_end_day(self):
        ad()
        assert renewals.open_due(today=END - timedelta(days=1)) == 0

    def test_never_twice_for_the_same_end_date(self):
        ad()
        renewals.open_due(today=END)
        assert renewals.open_due(today=END) == 0
        assert renewals.open_due(today=END + timedelta(days=1)) == 0
        assert AdRenewal.objects.count() == 1

    def test_a_missed_day_is_made_up_while_the_ad_is_still_marked_running(self):
        ad()
        assert renewals.open_due(today=END + timedelta(days=2)) == 1
        assert AdRenewal.objects.get().deadline == END + timedelta(days=5)

    @pytest.mark.parametrize('status', ['paused', 'cancelled', 'ended'])
    def test_only_running_ads_are_asked_about(self, status):
        ad(status=status)
        assert renewals.open_due(today=END) == 0

    def test_an_ad_that_was_never_paid_is_not_asked_about(self):
        ad(paid=False, status='scheduled')
        assert renewals.open_due(today=END) == 0

    def test_a_deleted_ad_is_not_asked_about(self):
        promotion = ad()
        promotion.soft_delete()
        assert renewals.open_due(today=END) == 0


class TestVisibility:
    def test_the_ad_stays_visible_until_the_deadline_while_the_answer_is_open(self):
        promotion = ad()
        renewals.open_due(today=END)
        for day in range(6):
            assert list(service.shown_now(END + timedelta(days=day))) == [promotion]
        assert list(service.shown_now(END + timedelta(days=6))) == []

    def test_without_a_renewal_the_ad_stops_after_its_end_date(self):
        ad()
        assert list(service.shown_now(END + timedelta(days=1))) == []

    def test_the_python_twin_agrees(self):
        promotion = ad()
        renewals.open_due(today=END)
        promotion = Promotion.objects.prefetch_related('renewals').get(pk=promotion.pk)
        assert service.is_shown_now(promotion, END + timedelta(days=5)) is True
        assert service.is_shown_now(promotion, END + timedelta(days=6)) is False

    def test_the_nightly_tidy_does_not_end_an_ad_with_an_open_renewal(self):
        promotion = ad()
        renewals.open_due(today=END)
        service.tidy_statuses(END + timedelta(days=1))
        promotion.refresh_from_db()
        assert promotion.status == 'active'

    def test_the_nightly_tidy_still_ends_an_ad_without_one(self):
        promotion = ad()
        service.tidy_statuses(END + timedelta(days=1))
        promotion.refresh_from_db()
        assert promotion.status == 'ended'


class TestReminders:
    def test_the_owner_hears_on_the_end_day_and_again_on_day_three(self):
        promotion = ad()
        renewals.open_due(today=END)
        for day in range(0, 6):
            renewals.send_reminders(today=END + timedelta(days=day))
        assert codes(promotion.property.owner) == ['ad_ending', 'ad_last_warning']

    def test_the_notice_carries_ids_and_dates_only(self):
        promotion = ad()
        renewals.open_due(today=END)
        renewals.send_reminders(today=END)
        assert Notification.objects.get().params == {
            'promotion_id': promotion.id, 'property_id': promotion.property_id,
            'end_date': '2026-11-30', 'until_date': '2026-12-05'}

    def test_after_a_gap_only_the_latest_reminder_is_sent(self):
        promotion = ad()
        renewals.open_due(today=END)
        renewals.send_reminders(today=END + timedelta(days=4))
        assert codes(promotion.property.owner) == ['ad_last_warning']

    def test_a_failing_notice_is_retried_and_never_raises(self):
        promotion = ad()
        renewals.open_due(today=END)
        with mock.patch('promotions.renewals.notify', side_effect=RuntimeError('boom')):
            assert renewals.send_reminders(today=END) == 0
        assert renewals.send_reminders(today=END + timedelta(days=1)) == 1
        assert codes(promotion.property.owner) == ['ad_ending']


class TestExpiry:
    def test_on_the_deadline_day_the_answer_is_still_open(self):
        ad()
        renewals.open_due(today=END)
        assert renewals.expire_overdue(today=END + timedelta(days=5)) == 0
        assert AdRenewal.objects.get().status == 'pending'

    def test_the_day_after_the_deadline_the_ad_is_removed_and_the_owner_told(self):
        promotion = ad()
        renewals.open_due(today=END)
        assert renewals.expire_overdue(today=END + timedelta(days=6)) == 1
        renewal, promotion = AdRenewal.objects.get(), Promotion.objects.get(pk=promotion.pk)
        assert (renewal.status, renewal.decided_via, renewal.decided_by, renewal.decided_at is not None) == (
            'expired', 'auto', None, True)
        assert (promotion.status, promotion.cancelled_reason) == ('cancelled', 'Not renewed in time')
        assert codes(promotion.property.owner) == ['ad_removed']
        assert list(service.shown_now(END + timedelta(days=6))) == []

    def test_the_hotel_itself_is_untouched(self):
        promotion = ad()
        renewals.open_due(today=END)
        renewals.expire_overdue(today=END + timedelta(days=6))
        promotion.property.refresh_from_db()
        assert promotion.property.status == 'active'

    def test_an_ad_cancelled_by_hand_meanwhile_just_closes_the_renewal(self):
        promotion = ad()
        renewals.open_due(today=END)
        service.cancel(promotion, actor=make_superadmin(), reason='Client asked')
        assert renewals.expire_overdue(today=END + timedelta(days=6)) == 1
        assert AdRenewal.objects.get().status == 'expired'
        assert codes(promotion.property.owner) == []


class TestConfirm:
    @pytest.fixture
    def boss(self):
        return make_superadmin()

    @pytest.mark.parametrize('end, expected', [
        (date(2026, 10, 31), date(2026, 11, 30)),
        (date(2026, 11, 30), date(2026, 12, 31)),
        (date(2026, 11, 15), date(2026, 12, 15)),
        (date(2026, 1, 31), date(2026, 2, 28)),
        (date(2026, 12, 31), date(2027, 1, 31)),
        (date(2026, 2, 28), date(2026, 3, 31)),
        (date(2026, 1, 30), date(2026, 2, 28)),
    ])
    def test_the_end_date_moves_one_month(self, boss, end, expected):
        assert renewals.next_month_end(end) == expected

    def test_confirming_extends_the_same_ad_and_records_who_and_how(self, boss):
        promotion = ad()
        renewals.open_due(today=END)
        renewals.confirm(AdRenewal.objects.get(), actor=boss)
        renewal, promotion = AdRenewal.objects.get(), Promotion.objects.get(pk=promotion.pk)
        assert promotion.end_date == date(2026, 12, 31) and promotion.status == 'active'
        assert (renewal.status, renewal.decided_by_id, renewal.decided_via) == ('renewed', boss.id, 'panel')
        assert codes(promotion.property.owner) == ['ad_renewed']
        row = AdminAccessLog.objects.get(action='ad_renewal_confirm')
        assert row.actor_id == boss.id and row.details['promotion_id'] == promotion.id

    def test_after_confirming_the_next_month_asks_again_on_the_new_end_day(self, boss):
        ad()
        renewals.open_due(today=END)
        renewals.confirm(AdRenewal.objects.get(), actor=boss)
        assert renewals.open_due(today=date(2026, 12, 31)) == 1
        assert AdRenewal.objects.filter(status='pending').get().ends_on == date(2026, 12, 31)

    def test_confirming_twice_or_after_expiry_is_refused(self, boss):
        ad()
        renewals.open_due(today=END)
        renewal = AdRenewal.objects.get()
        renewals.confirm(renewal, actor=boss)
        with pytest.raises(renewals.RenewalError) as twice:
            renewals.confirm(renewal, actor=boss)
        assert twice.value.code == 'already_decided'

    def test_an_extension_that_overlaps_another_ad_of_the_hotel_is_refused(self, boss):
        promotion = ad()
        later = Promotion.objects.create(
            property=promotion.property, start_date=END + timedelta(days=2), end_date=END + timedelta(days=30),
            status='scheduled')
        renewals.open_due(today=END)
        with pytest.raises(renewals.RenewalError) as clash:
            renewals.confirm(AdRenewal.objects.get(), actor=boss)
        assert clash.value.code == 'overlap'
        assert AdRenewal.objects.get().status == 'pending'
        assert Promotion.objects.get(pk=promotion.pk).end_date == END and later.pk

    def test_a_failing_notice_does_not_stop_the_confirmation(self, boss):
        ad()
        renewals.open_due(today=END)
        with mock.patch('promotions.renewals.notify', side_effect=RuntimeError('boom')):
            renewals.confirm(AdRenewal.objects.get(), actor=boss)
        assert AdRenewal.objects.get().status == 'renewed'


class TestDecline:
    def test_declining_removes_the_ad_now_and_tells_the_owner(self):
        boss = make_superadmin()
        promotion = ad()
        renewals.open_due(today=END)
        renewals.decline(AdRenewal.objects.get(), actor=boss)
        renewal, promotion = AdRenewal.objects.get(), Promotion.objects.get(pk=promotion.pk)
        assert (renewal.status, renewal.decided_by_id, renewal.decided_via) == ('declined', boss.id, 'panel')
        assert (promotion.status, promotion.cancelled_reason) == ('cancelled', 'Not renewed')
        assert codes(promotion.property.owner) == ['ad_removed']
        assert AdminAccessLog.objects.filter(action='ad_renewal_decline').count() == 1
        assert list(service.shown_now(END)) == []

    def test_declining_a_decided_renewal_is_refused(self):
        boss = make_superadmin()
        ad()
        renewals.open_due(today=END)
        renewal = AdRenewal.objects.get()
        renewals.decline(renewal, actor=boss)
        with pytest.raises(renewals.RenewalError):
            renewals.decline(renewal, actor=boss)


def test_the_daily_run_opens_expires_and_reminds_only_what_is_still_open():
    first = ad(end=END - timedelta(days=10))
    second = ad()
    result = renewals.run_daily(today=END)
    assert result == {'opened': 2, 'expired': 1, 'notices': 1}
    assert (Promotion.objects.get(pk=first.pk).status, Promotion.objects.get(pk=second.pk).status) == (
        'cancelled', 'active')
