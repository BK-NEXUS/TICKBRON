"""
R12 phase 3: Status numbers fed by the no-show workflow. no_show and no_show_reported hold
real values; an approved no-show is not a guest who stayed and is not revenue.
"""
from datetime import timedelta

import pytest

from bookings import metrics
from bookings.tests.r12b_helpers import A, COMMENT, DECISION, P, client_for, make_stay, past_stay, report_url, world  # noqa: F401


def report(world, booking):
    response = client_for(world['owner']).post(report_url(booking), {'comment': COMMENT}, format='json')
    assert response.status_code == 201, response.data
    return response.data['id']


def decide(world, report_id, action, callbacks=None):
    client = client_for(world['staff'])
    if callbacks is None:
        return client.post(f'{A}/no-show-reports/{report_id}/{action}/', {'decision_comment': DECISION}, format='json')
    with callbacks(execute=True):
        return client.post(f'{A}/no-show-reports/{report_id}/{action}/', {'decision_comment': DECISION}, format='json')


def totals(world):
    return metrics.metric_totals(metrics.all_bookings().filter(property=world['prop']), None, today=world['today'])


def money(rows):
    return {row['currency']: row['amount'] for row in rows}


@pytest.mark.django_db
class TestPendingReport:

    def test_counts_as_reported_not_confirmed(self, world):
        past_stay(world)                              # confirmed, no report
        reported = past_stay(world)                   # confirmed, pending report
        report(world, reported)
        t = totals(world)
        assert t['no_show_reported'] == 1
        assert t['booking_status']['no_show_reported'] == 1
        assert t['booking_status']['confirmed'] == 1             # not 2: the reported one is in its own bucket
        assert t['no_show'] == 0

    def test_a_completed_stay_with_a_pending_report_leaves_the_completed_count(self, world):
        past_stay(world, status='completed')
        report(world, past_stay(world, status='completed'))
        t = totals(world)
        assert t['booking_status']['completed'] == 1 and t['booking_status']['no_show_reported'] == 1

    def test_withdrawn_report_goes_back_to_its_status(self, world):
        booking = past_stay(world)
        report_id = report(world, booking)
        client_for(world['owner']).post(f'{P}/no-show-reports/{report_id}/withdraw/')
        t = totals(world)
        assert t['no_show_reported'] == 0 and t['booking_status']['confirmed'] == 1

    def test_rows_are_not_duplicated_by_old_reports(self, world):
        """Several reports of one booking (withdrawn, then pending) never multiply any count."""
        booking = past_stay(world, status='completed')
        first = report(world, booking)
        client_for(world['owner']).post(f'{P}/no-show-reports/{first}/withdraw/')
        report(world, booking)
        t = totals(world)
        assert (t['bookings'], t['guests'], t['nights']) == (1, 1, 2)
        assert t['no_show_reported'] == 1

    def test_outside_the_period_is_not_counted(self, world):
        report(world, past_stay(world))
        long_ago = (world['today'] + timedelta(days=100), world['today'] + timedelta(days=200))
        t = metrics.metric_totals(metrics.all_bookings().filter(property=world['prop']), long_ago, today=world['today'])
        assert t['no_show_reported'] == 0


@pytest.mark.django_db
class TestApprovedNoShow:

    def test_no_show_is_counted_and_is_not_a_guest_who_stayed(self, world, django_capture_on_commit_callbacks):
        past_stay(world, status='completed')           # one real stay
        booking = past_stay(world)
        decide(world, report(world, booking), 'approve', django_capture_on_commit_callbacks)
        t = totals(world)
        assert t['no_show'] == 1
        assert (t['bookings'], t['stayed'], t['guests'], t['nights']) == (1, 1, 1, 2)
        assert t['booking_status']['no_show'] == 1 and t['booking_status']['no_show_reported'] == 0

    def test_an_approved_no_show_is_not_revenue(self, world, django_capture_on_commit_callbacks):
        past_stay(world, status='completed')
        booking = past_stay(world)
        decide(world, report(world, booking), 'approve', django_capture_on_commit_callbacks)
        assert money(totals(world)['revenue']) == {'UZS': '2354590.00'}

    def test_reversing_the_approval_moves_the_booking_back_into_the_stay_numbers(
            self, world, django_capture_on_commit_callbacks):
        booking = past_stay(world)
        report_id = report(world, booking)
        decide(world, report_id, 'approve', django_capture_on_commit_callbacks)
        assert totals(world)['no_show'] == 1
        response = client_for(world['staff']).post(
            f'{A}/no-show-reports/{report_id}/reverse/', {'decision_comment': 'Mistake: the guest did come.'},
            format='json')
        assert response.status_code == 200
        t = totals(world)
        assert (t['no_show'], t['bookings'], t['stayed']) == (0, 1, 1)


@pytest.mark.django_db
class TestEndpoints:

    def test_admin_hotel_detail_carries_the_numbers(self, world, django_capture_on_commit_callbacks):
        decide(world, report(world, past_stay(world)), 'approve', django_capture_on_commit_callbacks)
        report(world, past_stay(world))
        data = client_for(world['staff']).get(f"{A}/status/hotels/{world['prop'].id}/?period=all").data
        assert data['totals']['no_show'] == 1 and data['totals']['no_show_reported'] == 1
        assert data['totals']['booking_status']['no_show'] == 1
        assert data['totals']['booking_status']['no_show_reported'] == 1

    def test_owner_status_carries_the_numbers(self, world, django_capture_on_commit_callbacks):
        decide(world, report(world, past_stay(world)), 'approve', django_capture_on_commit_callbacks)
        data = client_for(world['owner']).get(f"{P}/status/hotels/{world['prop'].id}/?period=all").data
        assert data['totals']['no_show'] == 1
        assert data['totals']['revenue'] == []
