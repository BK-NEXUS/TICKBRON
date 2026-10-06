"""
R12 phase 3: the no-show refund (NO_SHOW_REFUND_PERCENT, default 50).

- the percent is a snapshot on every booking, written in the inventory-locking transaction
- quote, booking creation and booking detail disclose percent, amount and a stable text key
- approving a report is ONE transaction (booking -> no_show, Refund rows, audit, notification);
  the provider is called after commit through the Refund service
- real mode: partial refunds are unverified with Payme/Click/Visa -> needs_manual;
  PAYMENT_TEST_MODE: the fake provider performs them
"""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError
from rest_framework.test import APIClient

from accounts.models import Notification
from bookings.models import Booking, NoShowReport
from bookings.noshow import approve_report
from bookings.tests.r12b_helpers import (
    A, COMMENT, DECISION, UZS_PRICE, client_for, make_stay, past_stay, pay, report_url, world,  # noqa: F401
)
from bookings.tests.test_quote import stay, quote  # noqa: F401  (fixtures: USD property, 60/69 USD nights)
from common.money import parse_percent
from payments.adapters import PaymeAdapter, PaymentAdapterError
from payments.models import PaymentTransaction, Refund
from properties.models import DateInventory, Property, RatePlan, RoomType


def report(world, booking, user=None):
    response = client_for(user or world['owner']).post(report_url(booking), {'comment': COMMENT}, format='json')
    assert response.status_code == 201, response.data
    return response.data['id']


def approve(world, report_id, callbacks, user=None, execute=True):
    with callbacks(execute=execute):
        return client_for(user or world['staff']).post(
            f'{A}/no-show-reports/{report_id}/approve/', {'decision_comment': DECISION}, format='json')


@pytest.mark.django_db
class TestSetting:

    def test_default_is_50(self, settings):
        assert settings.NO_SHOW_REFUND_PERCENT == 50

    @pytest.mark.parametrize('raw,expected', [('0', 0), ('50', 50), ('100', 100), (' 25 ', 25), (None, 50)])
    def test_parse_accepts_whole_percents(self, raw, expected):
        assert parse_percent('NO_SHOW_REFUND_PERCENT', raw, default=50) == expected

    @pytest.mark.parametrize('raw', ['-1', '101', '50.5', 'fifty', '', ' '])
    def test_startup_fails_outside_0_to_100(self, raw):
        with pytest.raises(ImproperlyConfigured):
            parse_percent('NO_SHOW_REFUND_PERCENT', raw, default=50)


@pytest.mark.django_db
class TestSnapshot:

    def _book(self, stay, client=None):
        client = client or client_for(stay['guest'])
        return client.post('/api/v1/bookings/', {
            'property_id': stay['property'].id, 'room_type_id': stay['room'].id,
            'rate_plan_id': stay['rate'].id, 'check_in': (stay['start'] + timedelta(days=1)).isoformat(),
            'check_out': (stay['start'] + timedelta(days=3)).isoformat(), 'guest_count': 1,
        }, format='json')

    def test_new_booking_snapshots_the_setting(self, stay, settings):
        settings.NO_SHOW_REFUND_PERCENT = 40
        response = self._book(stay)
        assert response.status_code == 201, response.data
        assert Booking.objects.get().no_show_refund_percent == 40

    def test_changing_the_setting_later_does_not_change_old_bookings(self, stay, settings):
        settings.NO_SHOW_REFUND_PERCENT = 50
        self._book(stay)
        settings.NO_SHOW_REFUND_PERCENT = 10
        booking = Booking.objects.get()
        assert booking.no_show_refund_percent == 50
        detail = client_for(stay['guest']).get(f'/api/v1/bookings/{booking.pk}/').data
        assert detail['no_show_refund_percent'] == 50

    def test_the_snapshot_cannot_be_changed_on_a_saved_booking(self, stay):
        self._book(stay)
        booking = Booking.objects.get()
        booking.no_show_refund_percent = 100
        with pytest.raises(PermissionError):
            booking.save()
        Booking.objects.get().refresh_from_db()
        assert Booking.objects.get().no_show_refund_percent == 50

    def test_rows_created_outside_create_booking_get_zero(self, world):
        booking = Booking.objects.create(
            guest=world['guest'], property=world['prop'], status='confirmed', payment_status='paid',
            check_in=world['today'] - timedelta(days=3), check_out=world['today'] - timedelta(days=1),
            number_of_nights=2, guest_count=1, total_price=Decimal('100'), currency='UZS', expires_at=None)
        assert booking.no_show_refund_percent == 0

    def test_snapshot_is_written_inside_the_inventory_locking_transaction(self, stay, settings):
        """If the booking cannot be created nothing is written; the percent is read with the rate."""
        settings.NO_SHOW_REFUND_PERCENT = 70
        with mock.patch('bookings.models.current_rate', return_value=None):
            response = self._book(stay)
        assert response.status_code == 503
        assert not Booking.objects.exists()

    def test_booking_percent_is_the_snapshot_of_the_creation_moment(self, stay, settings):
        settings.NO_SHOW_REFUND_PERCENT = 50
        self._book(stay)
        settings.NO_SHOW_REFUND_PERCENT = 0
        self._book(stay)
        assert sorted(Booking.objects.values_list('no_show_refund_percent', flat=True)) == [0, 50]


@pytest.mark.django_db
class TestDisclosure:

    def test_quote_carries_percent_amount_and_text_key(self, stay):
        data = quote(stay, 1, 3).data          # 60 + 69 = 129 USD -> uzs_total from the default test rate
        assert data['no_show_refund_percent'] == 50
        half = (Decimal(data['uzs_total']) * Decimal('0.5')).quantize(Decimal('1'), rounding='ROUND_HALF_UP')
        assert data['no_show_refund_amount'] == f'{half:.2f}'
        assert data['no_show_refund_text_key'] == 'no_show_refund_statement'
        assert data['no_show_refund_text_params'] == {'percent': 50, 'amount': f'{half:.2f}'}

    @pytest.mark.no_default_exchange_rate
    def test_quote_amount_is_null_without_a_rate(self, stay):
        data = quote(stay, 1, 3).data
        assert data['uzs_total'] is None
        assert data['no_show_refund_percent'] == 50 and data['no_show_refund_amount'] is None

    def test_quote_follows_the_setting(self, stay, settings):
        settings.NO_SHOW_REFUND_PERCENT = 0
        data = quote(stay, 1, 3).data
        assert data['no_show_refund_percent'] == 0
        assert data['no_show_refund_amount'] is None and data['no_show_refund_text_key'] is None

    def test_creation_response_and_detail_carry_the_stored_snapshot(self, stay):
        response = TestSnapshot()._book(stay)
        assert response.status_code == 201, response.data
        charge = Decimal(response.data['charge_amount'])
        expected = f"{(charge * Decimal('0.5')).quantize(Decimal('1'), rounding='ROUND_HALF_UP'):.2f}"
        for data in (response.data, client_for(stay['guest']).get(f"/api/v1/bookings/{response.data['id']}/").data,
                     client_for(stay['guest']).get('/api/v1/bookings/').data[0]):
            assert data['no_show_refund_percent'] == 50
            assert data['no_show_refund_amount'] == expected
            assert data['no_show_refund_text_key'] == 'no_show_refund_statement'
            assert data['no_show_refund_text_params'] == {'percent': 50, 'amount': expected}

    def test_old_booking_promises_nothing(self, world):
        booking = past_stay(world, percent=0)
        data = client_for(world['guest']).get(f'/api/v1/bookings/{booking.pk}/').data
        assert data['no_show_refund_percent'] == 0
        assert data['no_show_refund_amount'] is None and data['no_show_refund_text_key'] is None
        assert data['no_show_refund_text_params'] is None

    def test_amount_comes_from_the_snapshot_not_todays_rate(self, stay):
        response = TestSnapshot()._book(stay)
        booking = Booking.objects.get()
        from currency.cbu import tashkent_today
        from currency.models import ExchangeRate
        ExchangeRate.objects.create(currency='USD', rate=Decimal('99999'), nominal=1, source='cbu.uz',
                                    status='accepted', rate_date=tashkent_today() + timedelta(days=1))
        data = client_for(stay['guest']).get(f'/api/v1/bookings/{booking.pk}/').data
        assert data['no_show_refund_amount'] == response.data['no_show_refund_amount']

    def test_odd_amount_rounds_half_up(self, world):
        odd = make_stay(world['prop'], world['guest'], world['today'] - timedelta(days=4), nights=1,
                        price=Decimal('2354591'), room=world['room'], rate=world['rate'])
        data = client_for(world['guest']).get(f'/api/v1/bookings/{odd.pk}/').data
        assert data['no_show_refund_amount'] == '1177296.00'        # 1 177 295.5 -> half up


@pytest.mark.django_db
class TestApproveRefundAmount:

    def refund_for(self, world, booking, callbacks):
        response = approve(world, report(world, booking), callbacks)
        assert response.status_code == 200, response.data
        return list(Refund.objects.filter(booking=booking).order_by('id'))

    def test_half_of_the_amount_paid(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)               # paid 2 354 590, 50 %
        (refund,) = self.refund_for(world, booking, django_capture_on_commit_callbacks)
        assert refund.amount == Decimal('1177295') and refund.currency == 'UZS' and refund.reason == 'no_show'
        assert refund.idempotency_key == f'{booking.pk}:no_show'
        assert refund.created_by_id == world['staff'].id

    def test_odd_so_m_rounds_half_up(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world, nights=1, price=Decimal('2354591'))
        (refund,) = self.refund_for(world, booking, django_capture_on_commit_callbacks)
        assert refund.amount == Decimal('1177296')

    def test_percent_zero_creates_no_refund(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world, percent=0)
        assert self.refund_for(world, booking, django_capture_on_commit_callbacks) == []
        booking.refresh_from_db()
        assert booking.status == 'no_show'

    def test_booking_without_payment_creates_no_refund(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world, paid=False)
        assert self.refund_for(world, booking, django_capture_on_commit_callbacks) == []

    def test_several_payments_newest_first_never_more_than_each_has(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world, paid=False)
        old = pay(booking, amount=1000000)
        new = pay(booking, amount=400000)            # paid 1 400 000, target 700 000
        rows = self.refund_for(world, booking, django_capture_on_commit_callbacks)
        assert [(r.payment_id, r.amount) for r in rows] == [(new.id, Decimal('400000')), (old.id, Decimal('300000'))]
        assert sum(r.amount for r in rows) == Decimal('700000')
        keys = [r.idempotency_key for r in rows]
        assert keys[0] == f'{booking.pk}:no_show' and len(set(keys)) == 2

    def test_earlier_refund_is_subtracted(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        payment = booking.payments.get() if hasattr(booking, 'payments') else PaymentTransaction.objects.get()
        Refund.objects.create(payment=payment, booking=booking, amount=Decimal('200000'), currency='UZS',
                              reason='staff', status='succeeded', idempotency_key='earlier-1')
        (_, refund) = self.refund_for(world, booking, django_capture_on_commit_callbacks)
        assert refund.amount == Decimal('977295')            # 1 177 295 - 200 000
        total = sum(r.amount for r in Refund.objects.filter(booking=booking))
        assert total == Decimal('1177295')

    def test_earlier_refund_above_the_target_adds_nothing(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        payment = PaymentTransaction.objects.get()
        Refund.objects.create(payment=payment, booking=booking, amount=Decimal('2000000'), currency='UZS',
                              reason='staff', status='succeeded', idempotency_key='earlier-big')
        rows = self.refund_for(world, booking, django_capture_on_commit_callbacks)
        assert len(rows) == 1                                  # only the earlier one
        booking.refresh_from_db()
        assert booking.status == 'no_show'

    def test_earlier_failed_refund_does_not_count(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        payment = PaymentTransaction.objects.get()
        Refund.objects.create(payment=payment, booking=booking, amount=Decimal('900000'), currency='UZS',
                              reason='staff', status='failed', idempotency_key='earlier-failed')
        rows = self.refund_for(world, booking, django_capture_on_commit_callbacks)
        assert [r.amount for r in rows if r.reason == 'no_show'] == [Decimal('1177295')]

    def test_earlier_pending_and_needs_manual_refunds_count(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        payment = PaymentTransaction.objects.get()
        for index, status in enumerate(('pending', 'needs_manual')):
            Refund.objects.create(payment=payment, booking=booking, amount=Decimal('100000'), currency='UZS',
                                  reason='staff', status=status, idempotency_key=f'earlier-{index}')
        rows = self.refund_for(world, booking, django_capture_on_commit_callbacks)
        assert [r.amount for r in rows if r.reason == 'no_show'] == [Decimal('977295')]

    def test_percent_100_refunds_everything_still_unrefunded(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world, percent=100)
        payment = PaymentTransaction.objects.get()
        Refund.objects.create(payment=payment, booking=booking, amount=Decimal('354590'), currency='UZS',
                              reason='staff', status='succeeded', idempotency_key='earlier-100')
        rows = self.refund_for(world, booking, django_capture_on_commit_callbacks)
        assert sum(r.amount for r in rows) == Decimal('2354590')

    @pytest.mark.parametrize('percent', [0, 1, 33, 50, 99, 100])
    @pytest.mark.parametrize('paid', ['2354590', '2354591', '7'])
    def test_total_refunds_never_exceed_the_amount_paid(self, world, django_capture_on_commit_callbacks, percent, paid):
        booking = past_stay(world, percent=percent, nights=1, price=Decimal(paid))
        self.refund_for(world, booking, django_capture_on_commit_callbacks)
        total = sum((r.amount for r in Refund.objects.filter(booking=booking)), Decimal('0'))
        assert total <= Decimal(paid)

    def test_legacy_non_uzs_charge_gets_no_automatic_refund(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world, price=Decimal('100'), currency='USD')   # legacy: charged in USD at rate 1
        assert booking.charge_currency == 'USD'
        assert self.refund_for(world, booking, django_capture_on_commit_callbacks) == []


@pytest.mark.django_db
class TestApproveIsAtomicAndIdempotent:

    def test_second_approval_never_refunds_twice(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        report_id = report(world, booking)
        assert approve(world, report_id, django_capture_on_commit_callbacks).status_code == 200
        second = approve(world, report_id, django_capture_on_commit_callbacks)
        assert second.status_code == 400 and second.data['code'] == 'not_pending'
        assert Refund.objects.filter(booking=booking).count() == 1

    def test_an_existing_idempotency_key_is_reused_not_duplicated(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        payment = PaymentTransaction.objects.get()
        existing = Refund.objects.create(
            payment=payment, booking=booking, amount=Decimal('1177295'), currency='UZS', reason='no_show',
            status='succeeded', idempotency_key=f'{booking.pk}:no_show')
        response = approve(world, report(world, booking), django_capture_on_commit_callbacks)
        assert response.status_code == 200
        assert list(Refund.objects.filter(booking=booking)) == [existing]

    def test_provider_is_called_only_after_commit(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        report_id = report(world, booking)
        with mock.patch.object(PaymeAdapter, 'refund_payment', return_value={'success': True}) as provider:
            with django_capture_on_commit_callbacks(execute=False) as captured:
                response = client_for(world['staff']).post(
                    f'{A}/no-show-reports/{report_id}/approve/', {'decision_comment': DECISION}, format='json')
            assert response.status_code == 200
            provider.assert_not_called()                   # committed state only, nothing sent yet
            assert Refund.objects.get().status == 'pending'
            for callback in captured:                      # what the real commit would now run
                callback()
            provider.assert_called_once()
        assert Refund.objects.get().status == 'succeeded'

    def test_a_rolled_back_approval_calls_no_provider_and_changes_nothing(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        report_id = report(world, booking)
        row = NoShowReport.objects.get(pk=report_id)
        with mock.patch.object(PaymeAdapter, 'refund_payment') as provider, \
                mock.patch('bookings.noshow.notify', side_effect=RuntimeError('boom')):
            with django_capture_on_commit_callbacks(execute=True):
                with pytest.raises(RuntimeError):
                    approve_report(row.pk, world['staff'], DECISION)
            provider.assert_not_called()
        booking.refresh_from_db()
        assert booking.status == 'confirmed'
        assert NoShowReport.objects.get().status == 'pending'
        assert Refund.objects.count() == 0 and Notification.objects.count() == 0

    def test_test_mode_fake_provider_performs_the_partial_refund(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        assert approve(world, report(world, booking), django_capture_on_commit_callbacks).status_code == 200
        refund = Refund.objects.get()
        assert refund.status == 'succeeded' and refund.provider_reference
        payment = PaymentTransaction.objects.get()
        assert payment.status == 'partially_refunded'
        booking.refresh_from_db()
        assert booking.payment_status == 'partially_refunded'

    def test_real_mode_goes_to_needs_manual_and_never_calls_the_provider(
            self, world, settings, django_capture_on_commit_callbacks):
        settings.PAYMENT_TEST_MODE = False
        booking = past_stay(world)
        with mock.patch.object(PaymeAdapter, 'refund_payment') as provider:
            assert approve(world, report(world, booking), django_capture_on_commit_callbacks).status_code == 200
            provider.assert_not_called()
        refund = Refund.objects.get()
        assert refund.status == 'needs_manual' and refund.amount == Decimal('1177295')
        booking.refresh_from_db()
        assert booking.status == 'no_show'
        rows = client_for(world['staff']).get(f'{A}/refunds/needs-attention/').data['results']
        assert [row['id'] for row in rows] == [refund.id]
        # staff pays by hand and marks it done
        done = client_for(world['super']).post(
            f'{A}/refunds/{refund.id}/mark-done/', {'provider_reference': 'BANK-1'}, format='json')
        assert done.status_code == 200 and done.data['status'] == 'succeeded'
        assert PaymentTransaction.objects.get().status == 'partially_refunded'

    def test_provider_failure_leaves_the_booking_no_show_and_a_failed_refund_that_retries(
            self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        report_id = report(world, booking)
        with mock.patch.object(PaymeAdapter, 'refund_payment', side_effect=PaymentAdapterError('down')):
            response = approve(world, report_id, django_capture_on_commit_callbacks)
        assert response.status_code == 200                      # the decision stands
        refund = Refund.objects.get()
        assert refund.status == 'failed' and refund.error_code == 'REFUND_ERROR'
        booking.refresh_from_db()
        assert booking.status == 'no_show'
        rows = client_for(world['staff']).get(f'{A}/refunds/needs-attention/').data['results']
        assert [row['id'] for row in rows] == [refund.id]
        with mock.patch.object(PaymeAdapter, 'refund_payment', return_value={'success': True, 'id': 'r-9'}):
            retried = client_for(world['super']).post(f'{A}/refunds/{refund.id}/retry/')
        assert retried.status_code == 200 and retried.data['status'] == 'succeeded'
        assert Refund.objects.count() == 1                      # the same row, never a second refund

    def test_reject_moves_no_money_and_creates_no_refund(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        report_id = report(world, booking)
        with mock.patch.object(PaymeAdapter, 'refund_payment') as provider:
            with django_capture_on_commit_callbacks(execute=True):
                client_for(world['staff']).post(
                    f'{A}/no-show-reports/{report_id}/reject/', {'decision_comment': DECISION}, format='json')
            provider.assert_not_called()
        assert Refund.objects.count() == 0
        assert PaymentTransaction.objects.get().status == 'completed'

    def test_approve_response_describes_the_refund(self, world, django_capture_on_commit_callbacks):
        response = approve(world, report(world, past_stay(world)), django_capture_on_commit_callbacks)
        # the response is built before the test's captured on-commit send runs, so the status is not asserted here
        refund = Refund.objects.get()
        assert [(r['id'], r['amount'], r['currency']) for r in response.data['refunds']] == [
            (refund.id, '1177295.00', 'UZS')]
        detail = client_for(world['staff']).get(f"{A}/no-show-reports/{response.data['id']}/").data
        assert detail['refunds'][0]['status'] == 'succeeded'
