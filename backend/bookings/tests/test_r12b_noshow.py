"""
R12 phase 3: the no-show report workflow (the hotel reports, staff decide).

Owner: POST /partner/bookings/{id}/no-show-report/, GET /partner/no-show-reports/,
POST /partner/no-show-reports/{id}/withdraw/.
Staff: GET /admin-panel/no-show-reports/ (+ detail), POST .../{id}/approve|reject|reverse/.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.models import Notification
from admin_panel.models import AdminAccessLog
from bookings.completion import complete_finished_stays, finished_stays
from bookings.models import Booking, NoShowReport
from bookings.tests.r12b_helpers import (
    A, COMMENT, DECISION, P, client_for, make_stay, past_stay, report_url, world,  # noqa: F401
)
from payments.models import PaymentAuditLog, Refund
from properties.models import RoomInventory


def report(world, booking, comment=COMMENT, user=None):
    return client_for(user or world['owner']).post(report_url(booking), {'comment': comment}, format='json')


def decide(world, report_id, action, comment=DECISION, user=None):
    return client_for(user or world['staff']).post(
        f'{A}/no-show-reports/{report_id}/{action}/', {'decision_comment': comment}, format='json')


def approve(world, report_id, django_capture_on_commit_callbacks, comment=DECISION, user=None):
    with django_capture_on_commit_callbacks(execute=True):
        return decide(world, report_id, 'approve', comment, user)


@pytest.mark.django_db
class TestCreateReport:

    def test_owner_reports_a_confirmed_stay(self, world):
        booking = past_stay(world)
        response = report(world, booking)
        assert response.status_code == 201, response.data
        row = NoShowReport.objects.get()
        assert (row.booking_id, row.property_id, row.created_by_id, row.status) == (
            booking.id, world['prop'].id, world['owner'].id, 'pending')
        assert row.comment == COMMENT
        data = response.data
        assert data['status'] == 'pending' and data['booking_id'] == booking.id
        assert data['booking_reference'] == booking.confirmation_code
        # a pending report changes nothing on the booking
        booking.refresh_from_db()
        assert booking.status == 'confirmed'

    def test_owner_reports_a_completed_stay(self, world):
        booking = past_stay(world, status='completed')
        assert report(world, booking).status_code == 201

    @pytest.mark.parametrize('status', ['pending', 'cancelled', 'no_show'])
    def test_other_statuses_are_refused(self, world, status):
        booking = past_stay(world, status=status, paid=False)
        response = report(world, booking)
        assert response.status_code == 400
        assert response.data['code'] == 'not_reportable_status'
        assert NoShowReport.objects.count() == 0

    def test_check_in_day_itself_is_too_early(self, world):
        booking = make_stay(world['prop'], world['guest'], world['today'], nights=2,
                            room=world['room'], rate=world['rate'])
        response = report(world, booking)
        assert response.status_code == 400 and response.data['code'] == 'too_early'

    def test_day_after_check_in_is_allowed(self, world):
        booking = make_stay(world['prop'], world['guest'], world['today'] - timedelta(days=1), nights=3,
                            room=world['room'], rate=world['rate'])
        assert report(world, booking).status_code == 201

    def test_window_after_check_out(self, world, settings):
        settings.NO_SHOW_REPORT_WINDOW_DAYS = 7
        # check-out exactly 7 days ago: last day inside the window
        inside = past_stay(world, days_ago_check_in=9, nights=2, status='completed')
        assert report(world, inside).status_code == 201
        # check-out 8 days ago: closed
        outside = past_stay(world, days_ago_check_in=10, nights=2, status='completed')
        response = report(world, outside)
        assert response.status_code == 400 and response.data['code'] == 'window_closed'

    def test_window_follows_the_setting(self, world, settings):
        settings.NO_SHOW_REPORT_WINDOW_DAYS = 2
        booking = past_stay(world, days_ago_check_in=6, nights=2, status='completed')  # check-out 4 days ago
        assert report(world, booking).data['code'] == 'window_closed'

    @pytest.mark.parametrize('comment', ['', 'too short', 'x' * 501, None])
    def test_comment_length_is_10_to_500(self, world, comment):
        booking = past_stay(world)
        response = client_for(world['owner']).post(report_url(booking), {'comment': comment}, format='json')
        assert response.status_code == 400
        assert 'comment' in response.data
        assert NoShowReport.objects.count() == 0

    def test_comment_boundaries_are_accepted(self, world):
        first, second = past_stay(world), past_stay(world)
        assert report(world, first, comment='x' * 10).status_code == 201
        assert report(world, second, comment='y' * 500).status_code == 201

    def test_comment_is_stripped_and_plain_text(self, world):
        booking = past_stay(world)
        assert report(world, booking, comment='   padded comment text   ').status_code == 201
        assert NoShowReport.objects.get().comment == 'padded comment text'

    @pytest.mark.parametrize('comment', ['<b>bold</b> guest never came', 'see <script>alert(1)</script> ok'])
    def test_html_is_refused(self, world, comment):
        response = report(world, past_stay(world), comment=comment)
        assert response.status_code == 400 and 'comment' in response.data

    def test_blank_padding_does_not_count_towards_the_minimum(self, world):
        response = report(world, past_stay(world), comment='   short   ')
        assert response.status_code == 400

    def test_second_report_for_the_same_booking_is_refused(self, world):
        booking = past_stay(world)
        assert report(world, booking).status_code == 201
        response = report(world, booking)
        assert response.status_code == 400 and response.data['code'] == 'report_exists'
        assert NoShowReport.objects.count() == 1

    def test_database_allows_one_pending_report_per_booking(self, world):
        booking = past_stay(world)
        make = lambda: NoShowReport.objects.create(
            booking=booking, property=world['prop'], created_by=world['owner'], comment=COMMENT)
        make()
        with pytest.raises(IntegrityError), transaction.atomic():
            make()

    def test_a_withdrawn_report_can_be_filed_again(self, world):
        booking = past_stay(world)
        first = report(world, booking).data['id']
        assert client_for(world['owner']).post(f'{P}/no-show-reports/{first}/withdraw/').status_code == 200
        assert report(world, booking).status_code == 201
        assert NoShowReport.objects.filter(booking=booking).count() == 2

    def test_a_decided_report_blocks_a_new_one(self, world):
        booking = past_stay(world)
        report_id = report(world, booking).data['id']
        assert decide(world, report_id, 'reject').status_code == 200
        response = report(world, booking)
        assert response.status_code == 400 and response.data['code'] == 'report_exists'

    def test_owner_cannot_report_another_owners_booking(self, world):
        other = make_stay(world['other_prop'], world['guest'], world['today'] - timedelta(days=3),
                          room=world['other_room'], rate=world['other_rate'])
        response = report(world, other)
        assert response.status_code == 404
        assert NoShowReport.objects.count() == 0

    def test_unknown_and_deleted_bookings_are_404(self, world):
        assert client_for(world['owner']).post(f'{P}/bookings/999999/no-show-report/', {'comment': COMMENT},
                                               format='json').status_code == 404
        booking = past_stay(world)
        Booking.objects.filter(pk=booking.pk).update(is_deleted=True)
        assert report(world, booking).status_code == 404

    def test_staff_do_not_report_other_hotels_bookings(self, world):
        # IsHotelOwner lets staff in, but they only ever see hotels they own
        assert report(world, past_stay(world), user=world['staff']).status_code == 404

    def test_guest_cannot_report(self, world):
        assert report(world, past_stay(world), user=world['guest']).status_code == 403

    def test_anonymous_is_rejected(self, world):
        booking = past_stay(world)
        response = client_for(None).post(report_url(booking), {'comment': COMMENT}, format='json')
        assert response.status_code in (401, 403)

    def test_report_endpoint_is_rate_limited(self):
        from bookings.views_noshow import NoShowReportThrottle
        assert NoShowReportThrottle.scope == 'no_show_report'
        from django.conf import settings
        assert settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['no_show_report'] == '20/hour'

    def test_rate_limit_triggers(self, world, monkeypatch):
        from django.core.cache import cache
        from rest_framework.throttling import UserRateThrottle
        import bookings.views_noshow as module
        cache.clear()
        monkeypatch.setattr(module, 'TESTING', False)
        monkeypatch.setattr(UserRateThrottle, 'THROTTLE_RATES',
                            {**UserRateThrottle.THROTTLE_RATES, 'no_show_report': '2/hour'})
        booking = past_stay(world)
        codes = [client_for(world['owner']).post(report_url(booking), {'comment': COMMENT}, format='json')
                 .status_code for _ in range(4)]
        cache.clear()
        assert 429 in codes


@pytest.mark.django_db
class TestOwnerReports:

    def test_list_shows_only_own_reports_with_filters(self, world):
        mine = report(world, past_stay(world)).data['id']
        mine_withdrawn = report(world, past_stay(world)).data['id']
        client_for(world['owner']).post(f'{P}/no-show-reports/{mine_withdrawn}/withdraw/')
        other = make_stay(world['other_prop'], world['guest'], world['today'] - timedelta(days=3),
                          room=world['other_room'], rate=world['other_rate'])
        report(world, other, user=world['other_owner'])

        owner = client_for(world['owner'])
        rows = owner.get(f'{P}/no-show-reports/').data['results']
        assert {row['id'] for row in rows} == {mine, mine_withdrawn}
        pending = owner.get(f'{P}/no-show-reports/?status=pending').data['results']
        assert [row['id'] for row in pending] == [mine]
        by_property = owner.get(f'{P}/no-show-reports/?property={world["prop"].id}').data['results']
        assert len(by_property) == 2
        assert owner.get(f'{P}/no-show-reports/?property={world["other_prop"].id}').data['results'] == []
        assert owner.get(f'{P}/no-show-reports/?status=bogus').status_code == 400

    def test_row_shape_has_no_personal_data(self, world):
        booking = past_stay(world)
        report(world, booking)
        row = client_for(world['owner']).get(f'{P}/no-show-reports/').data['results'][0]
        assert set(row) == {
            'id', 'booking_id', 'booking_reference', 'property_id', 'property_name', 'check_in', 'check_out',
            'comment', 'status', 'decision_comment', 'decided_at', 'created_at',
        }
        assert row['decision_comment'] == '' and row['decided_at'] is None

    def test_owner_sees_the_decision_comment(self, world, django_capture_on_commit_callbacks):
        report_id = report(world, past_stay(world)).data['id']
        approve(world, report_id, django_capture_on_commit_callbacks)
        row = client_for(world['owner']).get(f'{P}/no-show-reports/').data['results'][0]
        assert row['status'] == 'approved' and row['decision_comment'] == DECISION and row['decided_at']

    def test_withdraw_own_pending_report(self, world):
        booking = past_stay(world)
        report_id = report(world, booking).data['id']
        response = client_for(world['owner']).post(f'{P}/no-show-reports/{report_id}/withdraw/')
        assert response.status_code == 200 and response.data['status'] == 'withdrawn'
        assert NoShowReport.objects.get().status == 'withdrawn'
        booking.refresh_from_db()
        assert booking.status == 'confirmed'

    def test_withdraw_twice_and_after_a_decision_is_refused(self, world):
        first = report(world, past_stay(world)).data['id']
        second = report(world, past_stay(world)).data['id']
        owner = client_for(world['owner'])
        owner.post(f'{P}/no-show-reports/{first}/withdraw/')
        again = owner.post(f'{P}/no-show-reports/{first}/withdraw/')
        assert again.status_code == 400 and again.data['code'] == 'not_pending'
        decide(world, second, 'reject')
        late = owner.post(f'{P}/no-show-reports/{second}/withdraw/')
        assert late.status_code == 400 and late.data['code'] == 'not_pending'

    def test_withdraw_another_owners_report_is_404(self, world):
        other = make_stay(world['other_prop'], world['guest'], world['today'] - timedelta(days=3),
                          room=world['other_room'], rate=world['other_rate'])
        report_id = report(world, other, user=world['other_owner']).data['id']
        assert client_for(world['owner']).post(f'{P}/no-show-reports/{report_id}/withdraw/').status_code == 404
        assert NoShowReport.objects.get().status == 'pending'

    def test_owner_cannot_decide(self, world):
        report_id = report(world, past_stay(world)).data['id']
        for action in ('approve', 'reject', 'reverse'):
            assert decide(world, report_id, action, user=world['owner']).status_code == 403
        assert client_for(world['owner']).get(f'{A}/no-show-reports/').status_code == 403
        assert client_for(world['owner']).get(f'{A}/no-show-reports/{report_id}/').status_code == 403
        assert NoShowReport.objects.get().status == 'pending'


@pytest.mark.django_db
class TestStaffQueue:

    def test_pending_first_oldest_first(self, world, django_capture_on_commit_callbacks):
        ids = [report(world, past_stay(world)).data['id'] for _ in range(3)]
        approve(world, ids[0], django_capture_on_commit_callbacks)         # the oldest, now decided
        rows = client_for(world['staff']).get(f'{A}/no-show-reports/').data['results']
        assert [row['id'] for row in rows] == [ids[1], ids[2], ids[0]]

    def test_filters(self, world):
        first = report(world, past_stay(world)).data['id']
        other = make_stay(world['other_prop'], world['guest'], world['today'] - timedelta(days=3),
                          room=world['other_room'], rate=world['other_rate'])
        second = report(world, other, user=world['other_owner']).data['id']
        decide(world, first, 'reject')
        staff = client_for(world['staff'])
        assert [r['id'] for r in staff.get(f'{A}/no-show-reports/?status=pending').data['results']] == [second]
        assert [r['id'] for r in staff.get(f'{A}/no-show-reports/?status=rejected').data['results']] == [first]
        by_property = staff.get(f'{A}/no-show-reports/?property={world["other_prop"].id}').data['results']
        assert [r['id'] for r in by_property] == [second]
        day = world['today'].isoformat()
        assert len(staff.get(f'{A}/no-show-reports/?from={day}&to={day}').data['results']) == 2
        tomorrow = (world['today'] + timedelta(days=1)).isoformat()
        assert staff.get(f'{A}/no-show-reports/?from={tomorrow}').data['results'] == []
        assert staff.get(f'{A}/no-show-reports/?from=nonsense').status_code == 400

    def test_row_carries_booking_hotel_comment_and_the_exact_refund(self, world):
        booking = past_stay(world)           # 2 354 590 paid, 50 %
        report(world, booking)
        row = client_for(world['staff']).get(f'{A}/no-show-reports/').data['results'][0]
        assert row['booking_reference'] == booking.confirmation_code
        assert row['property_id'] == world['prop'].id and row['property_name']
        assert (row['check_in'], row['check_out']) == (booking.check_in.isoformat(), booking.check_out.isoformat())
        assert row['comment'] == COMMENT
        assert row['hotel_flagged'] is False
        assert row['refund_preview'] == {
            'amount': '1177295.00', 'currency': 'UZS', 'percent': 50,
            'already_refunded': '0.00', 'paid': '2354590.00',
        }

    def test_row_has_no_guest_personal_data(self, world):
        report(world, past_stay(world))
        text = str(client_for(world['staff']).get(f'{A}/no-show-reports/').data)
        for private in ('guest@example.com', 'Gita', 'Test Guest', '+998'):
            assert private not in text

    def test_detail(self, world):
        report_id = report(world, past_stay(world)).data['id']
        staff = client_for(world['staff'])
        data = staff.get(f'{A}/no-show-reports/{report_id}/').data
        assert data['id'] == report_id and data['refund_preview']['amount'] == '1177295.00'
        assert staff.get(f'{A}/no-show-reports/999999/').status_code == 404

    def test_old_booking_without_a_promise_previews_zero(self, world):
        report(world, past_stay(world, percent=0))
        row = client_for(world['staff']).get(f'{A}/no-show-reports/').data['results'][0]
        assert row['refund_preview']['amount'] == '0.00' and row['refund_preview']['percent'] == 0


@pytest.mark.django_db
class TestDecisions:

    def test_approve_marks_the_booking_no_show(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        report_id = report(world, booking).data['id']
        response = approve(world, report_id, django_capture_on_commit_callbacks)
        assert response.status_code == 200, response.data
        assert response.data['status'] == 'approved'
        booking.refresh_from_db()
        assert booking.status == 'no_show'
        row = NoShowReport.objects.get()
        assert (row.status, row.decided_by_id, row.decision_comment) == ('approved', world['staff'].id, DECISION)
        assert row.decided_at is not None

    def test_approve_a_completed_stay(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world, status='completed')
        report_id = report(world, booking).data['id']
        assert approve(world, report_id, django_capture_on_commit_callbacks).status_code == 200
        booking.refresh_from_db()
        assert booking.status == 'no_show'

    def test_completed_to_no_show_only_through_an_approved_report(self, world):
        booking = past_stay(world, status='completed')
        with pytest.raises(Exception):
            booking.mark_no_show()
        booking.refresh_from_db()
        assert booking.status == 'completed'

    def test_approve_logs_the_state_change_and_an_audit_row_with_ids_only(
            self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        report_id = report(world, booking).data['id']
        approve(world, report_id, django_capture_on_commit_callbacks)
        change = PaymentAuditLog.objects.filter(booking=booking, action='booking_status_changed').get()
        assert (change.old_status, change.new_status) == ('confirmed', 'no_show')
        audit = AdminAccessLog.objects.get(action='no_show_report_approve')
        assert audit.actor_id == world['staff'].id and audit.target_booking_id == booking.id
        assert audit.details == {'report_id': report_id}
        assert DECISION not in str(audit.details) and audit.target_user_id is None

    def test_reject_changes_nothing_and_moves_no_money(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        report_id = report(world, booking).data['id']
        with django_capture_on_commit_callbacks(execute=True):
            response = decide(world, report_id, 'reject')
        assert response.status_code == 200 and response.data['status'] == 'rejected'
        booking.refresh_from_db()
        assert booking.status == 'confirmed'
        assert Refund.objects.count() == 0
        row = NoShowReport.objects.get()
        assert (row.status, row.decided_by_id, row.decision_comment) == ('rejected', world['staff'].id, DECISION)
        assert AdminAccessLog.objects.filter(action='no_show_report_reject').count() == 1

    @pytest.mark.parametrize('comment', ['', 'short', 'x' * 501, None])
    @pytest.mark.parametrize('action', ['approve', 'reject'])
    def test_decision_comment_is_required_10_to_500(self, world, action, comment):
        booking = past_stay(world)
        report_id = report(world, booking).data['id']
        response = decide(world, report_id, action, comment=comment)
        assert response.status_code == 400 and 'decision_comment' in response.data
        assert NoShowReport.objects.get().status == 'pending'
        booking.refresh_from_db()
        assert booking.status == 'confirmed' and Refund.objects.count() == 0

    def test_decision_on_a_decided_report_is_refused(self, world, django_capture_on_commit_callbacks):
        report_id = report(world, past_stay(world)).data['id']
        approve(world, report_id, django_capture_on_commit_callbacks)
        for action in ('approve', 'reject'):
            response = decide(world, report_id, action)
            assert response.status_code == 400 and response.data['code'] == 'not_pending'

    def test_unknown_report_is_404(self, world):
        assert decide(world, 999999, 'approve').status_code == 404

    def test_a_booking_cancelled_meanwhile_cannot_be_approved(self, world):
        booking = past_stay(world)
        report_id = report(world, booking).data['id']
        Booking.objects.filter(pk=booking.pk).update(status='cancelled')
        response = decide(world, report_id, 'approve')
        assert response.status_code == 400 and response.data['code'] == 'booking_not_reportable'
        assert NoShowReport.objects.get().status == 'pending'
        assert Refund.objects.count() == 0

    def test_super_admin_decides_too(self, world, django_capture_on_commit_callbacks):
        report_id = report(world, past_stay(world)).data['id']
        assert approve(world, report_id, django_capture_on_commit_callbacks, user=world['super']).status_code == 200


@pytest.mark.django_db
class TestReverse:

    def test_approved_to_rejected_restores_the_booking_and_keeps_the_money(
            self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)     # check-out in the past -> back to completed
        report_id = report(world, booking).data['id']
        approve(world, report_id, django_capture_on_commit_callbacks)
        refund = Refund.objects.get()
        with django_capture_on_commit_callbacks(execute=True):
            response = decide(world, report_id, 'reverse', comment='Mistake: the guest did arrive late.')
        assert response.status_code == 200 and response.data['status'] == 'rejected'
        booking.refresh_from_db()
        assert booking.status == 'completed'
        # money already refunded is not taken back; no second refund row
        assert Refund.objects.count() == 1 and Refund.objects.get().pk == refund.pk
        assert AdminAccessLog.objects.filter(action='no_show_report_reverse').count() == 1
        # the guest is not notified a second time
        assert Notification.objects.filter(code='no_show_marked').count() == 1

    def test_reverse_before_check_out_goes_back_to_confirmed(self, world, django_capture_on_commit_callbacks):
        booking = make_stay(world['prop'], world['guest'], world['today'] - timedelta(days=1), nights=3,
                            room=world['room'], rate=world['rate'])
        report_id = report(world, booking).data['id']
        approve(world, report_id, django_capture_on_commit_callbacks)
        decide(world, report_id, 'reverse', comment='Mistake: the guest did arrive.')
        booking.refresh_from_db()
        assert booking.status == 'confirmed'

    def test_rejected_to_approved_refunds_once(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        report_id = report(world, booking).data['id']
        decide(world, report_id, 'reject')
        with django_capture_on_commit_callbacks(execute=True):
            response = decide(world, report_id, 'reverse', comment='Second look: guest did not arrive.')
        assert response.status_code == 200 and response.data['status'] == 'approved'
        booking.refresh_from_db()
        assert booking.status == 'no_show'
        assert Refund.objects.get().amount == Decimal('1177295')

    def test_reverse_twice_flips_back_but_never_refunds_twice(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        report_id = report(world, booking).data['id']
        approve(world, report_id, django_capture_on_commit_callbacks)
        for comment in ('Mistake: guest did arrive.', 'Mistake again: guest did not arrive.'):
            with django_capture_on_commit_callbacks(execute=True):
                assert decide(world, report_id, 'reverse', comment=comment).status_code == 200
        assert NoShowReport.objects.get().status == 'approved'
        assert Refund.objects.count() == 1

    def test_reverse_needs_a_decided_report_and_a_comment(self, world):
        report_id = report(world, past_stay(world)).data['id']
        response = decide(world, report_id, 'reverse', comment='Trying to reverse a pending one.')
        assert response.status_code == 400 and response.data['code'] == 'not_decided'
        decide(world, report_id, 'reject')
        assert decide(world, report_id, 'reverse', comment='').status_code == 400

    def test_a_withdrawn_report_cannot_be_reversed(self, world):
        report_id = report(world, past_stay(world)).data['id']
        client_for(world['owner']).post(f'{P}/no-show-reports/{report_id}/withdraw/')
        response = decide(world, report_id, 'reverse', comment='Trying to reverse a withdrawn one.')
        assert response.status_code == 400 and response.data['code'] == 'not_decided'


@pytest.mark.django_db
class TestPendingReportBlocksCompletion:

    def test_auto_completion_skips_a_pending_report(self, world):
        blocked = past_stay(world)
        free = past_stay(world)
        report(world, blocked)
        assert [b.pk for b in finished_stays()] == [free.pk]
        result = complete_finished_stays()
        assert result['changed'] == 1
        blocked.refresh_from_db(), free.refresh_from_db()
        assert (blocked.status, free.status) == ('confirmed', 'completed')

    def test_dry_run_counts_exclude_the_blocked_booking(self, world):
        report(world, past_stay(world))
        assert complete_finished_stays(dry_run=True)['eligible'] == 0

    def test_rejected_or_withdrawn_report_lets_the_next_run_complete(self, world):
        first, second = past_stay(world), past_stay(world)
        first_report = report(world, first).data['id']
        second_report = report(world, second).data['id']
        decide(world, first_report, 'reject')
        client_for(world['owner']).post(f'{P}/no-show-reports/{second_report}/withdraw/')
        assert complete_finished_stays()['changed'] == 2
        first.refresh_from_db(), second.refresh_from_db()
        assert (first.status, second.status) == ('completed', 'completed')

    def test_after_a_rejected_report_the_completed_stay_cannot_be_reported_again(self, world):
        booking = past_stay(world)
        report_id = report(world, booking).data['id']
        decide(world, report_id, 'reject')
        complete_finished_stays()
        assert report(world, booking).data['code'] == 'report_exists'


@pytest.mark.django_db
class TestFutureNightsAreReleased:

    def _inventory(self, world, start, nights, booked):
        for offset in range(nights):
            RoomInventory.objects.create(room_type=world['room'], date=start + timedelta(days=offset),
                                         available_rooms=3, booked_rooms=booked)

    def test_approval_releases_only_nights_after_today(self, world, django_capture_on_commit_callbacks):
        start = world['today'] - timedelta(days=1)             # 4 nights: 2 past or today, 2 future
        booking = make_stay(world['prop'], world['guest'], start, nights=4, room=world['room'],
                            rate=world['rate'], rooms=2)
        self._inventory(world, start, 4, booked=2)
        report_id = report(world, booking).data['id']
        approve(world, report_id, django_capture_on_commit_callbacks)
        booked = {row.date: row.booked_rooms for row in RoomInventory.objects.all()}
        assert booked[start] == 2 and booked[start + timedelta(days=1)] == 2      # yesterday, today: kept
        assert booked[start + timedelta(days=2)] == 0 and booked[start + timedelta(days=3)] == 0

    def test_a_finished_stay_changes_no_inventory(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        self._inventory(world, booking.check_in, 2, booked=1)
        report_id = report(world, booking).data['id']
        approve(world, report_id, django_capture_on_commit_callbacks)
        assert {row.booked_rooms for row in RoomInventory.objects.all()} == {1}

    def test_reverse_reserves_the_nights_again_when_there_is_room(self, world, django_capture_on_commit_callbacks):
        start = world['today'] - timedelta(days=1)
        booking = make_stay(world['prop'], world['guest'], start, nights=3, room=world['room'], rate=world['rate'])
        self._inventory(world, start, 3, booked=1)
        report_id = report(world, booking).data['id']
        approve(world, report_id, django_capture_on_commit_callbacks)
        assert RoomInventory.objects.get(date=start + timedelta(days=2)).booked_rooms == 0
        decide(world, report_id, 'reverse', comment='Mistake: the guest did arrive.')
        assert RoomInventory.objects.get(date=start + timedelta(days=2)).booked_rooms == 1

    def test_reverse_is_refused_when_the_nights_were_resold(self, world, django_capture_on_commit_callbacks):
        start = world['today'] - timedelta(days=1)
        booking = make_stay(world['prop'], world['guest'], start, nights=3, room=world['room'], rate=world['rate'])
        self._inventory(world, start, 3, booked=1)
        report_id = report(world, booking).data['id']
        approve(world, report_id, django_capture_on_commit_callbacks)
        RoomInventory.objects.filter(date=start + timedelta(days=2)).update(booked_rooms=3)   # sold out again
        response = decide(world, report_id, 'reverse', comment='Mistake: the guest did arrive.')
        assert response.status_code == 400 and response.data['code'] == 'inventory_unavailable'
        assert NoShowReport.objects.get().status == 'approved'
        booking.refresh_from_db()
        assert booking.status == 'no_show'


@pytest.mark.django_db
class TestNotifications:

    def test_owner_and_guest_notified_on_approval(self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        report_id = report(world, booking).data['id']
        approve(world, report_id, django_capture_on_commit_callbacks)
        owner_note = Notification.objects.get(user=world['owner'])
        assert owner_note.code == 'no_show_report_approved'
        assert owner_note.params == {'report_id': report_id, 'booking_id': booking.id,
                                     'booking_reference': booking.confirmation_code}
        guest_note = Notification.objects.get(user=world['guest'])
        assert guest_note.code == 'no_show_marked'
        assert guest_note.params == {
            'booking_id': booking.id, 'booking_reference': booking.confirmation_code,
            'amount': '1177295', 'currency': 'UZS', 'percent': 50,
        }
        assert guest_note.booking_id == booking.id

    def test_guest_without_a_promised_refund_gets_the_no_refund_notice(
            self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world, percent=0)
        approve(world, report(world, booking).data['id'], django_capture_on_commit_callbacks)
        note = Notification.objects.get(user=world['guest'])
        assert note.code == 'no_show_marked_no_refund'
        assert note.params == {'booking_id': booking.id, 'booking_reference': booking.confirmation_code}

    def test_owner_only_is_notified_on_rejection(self, world):
        booking = past_stay(world)
        report_id = report(world, booking).data['id']
        decide(world, report_id, 'reject')
        note = Notification.objects.get(user=world['owner'])
        assert note.code == 'no_show_report_rejected'
        assert note.params['report_id'] == report_id
        assert not Notification.objects.filter(user=world['guest']).exists()

    def test_notifications_hold_no_free_text(self, world, django_capture_on_commit_callbacks):
        approve(world, report(world, past_stay(world)).data['id'], django_capture_on_commit_callbacks)
        for note in Notification.objects.all():
            assert COMMENT not in str(note.params) and DECISION not in str(note.params)
            assert COMMENT not in note.message and DECISION not in note.message


@pytest.mark.django_db
class TestAbuseFlag:

    def _reports(self, world, count, prop=None, room=None, rate=None, owner=None):
        prop, room, rate, owner = prop or world['prop'], room or world['room'], rate or world['rate'], \
            owner or world['owner']
        for _ in range(count):
            booking = make_stay(prop, world['guest'], world['today'] - timedelta(days=3), room=room, rate=rate)
            report(world, booking, user=owner)

    def _normal_traffic(self, world, count):
        """Plenty of ordinary stays at the other hotel (no reports) so the platform average is small."""
        for _ in range(count):
            make_stay(world['other_prop'], world['guest'], world['today'] - timedelta(days=5), status='completed',
                      room=world['other_room'], rate=world['other_rate'], paid=False)

    def flagged(self, world):
        rows = client_for(world['staff']).get(f'{A}/no-show-reports/').data['results']
        return {row['property_id']: row['hotel_flagged'] for row in rows}

    def test_hotel_with_many_reports_is_flagged(self, world):
        self._normal_traffic(world, 100)
        self._reports(world, 5)
        assert self.flagged(world) == {world['prop'].id: True}

    def test_fewer_than_the_minimum_reports_is_not_flagged(self, world):
        self._normal_traffic(world, 100)
        self._reports(world, 4)
        assert self.flagged(world) == {world['prop'].id: False}

    def test_thresholds_are_settings(self, world, settings):
        settings.NO_SHOW_FLAG_MIN_REPORTS = 2
        self._normal_traffic(world, 100)
        self._reports(world, 2)
        assert self.flagged(world) == {world['prop'].id: True}
        settings.NO_SHOW_FLAG_FACTOR = 100000
        assert self.flagged(world) == {world['prop'].id: False}

    def test_minimum_rate_floor(self, world, settings):
        # 5 reports in 60 bookings = 8.3 %: well above 3x the platform average (1.9 %) but below the 10 % floor
        self._normal_traffic(world, 200)
        self._reports(world, 5)
        for _ in range(55):
            make_stay(world['prop'], world['guest'], world['today'] - timedelta(days=5), status='completed',
                      room=world['room'], rate=world['rate'], paid=False)
        assert self.flagged(world) == {world['prop'].id: False}
        settings.NO_SHOW_FLAG_MIN_RATE = '0.05'
        assert self.flagged(world) == {world['prop'].id: True}

    def test_similar_rates_are_not_flagged(self, world):
        # both hotels report at the same rate: nobody is 3x the average
        self._reports(world, 5)
        self._reports(world, 5, prop=world['other_prop'], room=world['other_room'], rate=world['other_rate'],
                      owner=world['other_owner'])
        assert set(self.flagged(world).values()) == {False}

    def test_reports_older_than_the_window_do_not_count(self, world):
        self._normal_traffic(world, 100)
        self._reports(world, 5)
        NoShowReport.objects.all().update(created_at=timezone.now() - timedelta(days=200))
        self._reports(world, 1)
        assert self.flagged(world) == {world['prop'].id: False}
