"""R12 phase 3: the owner's bookings list says which bookings can be reported as no-show."""
from datetime import timedelta

import pytest
from django.conf import settings

from bookings.models import NoShowReport
from bookings.tests.r12b_helpers import COMMENT, P, client_for, make_stay, past_stay, world  # noqa: F401

WINDOW = settings.NO_SHOW_REPORT_WINDOW_DAYS


def listing(world, query=''):
    response = client_for(world['owner']).get(f'{P}/bookings/{query}')
    assert response.status_code == 200
    return {row['id']: row for row in response.json()}


def stay_ending(world, days_after_check_out, nights=2, **kwargs):
    """A stay whose check-out was `days_after_check_out` days ago."""
    check_in = world['today'] - timedelta(days=nights + days_after_check_out)
    return make_stay(world['prop'], world['guest'], check_in, nights=nights, room=world['room'],
                     rate=world['rate'], **kwargs)


@pytest.mark.django_db
class TestCanReportNoShow:
    def test_check_in_day_is_too_early(self, world):
        booking = past_stay(world, days_ago_check_in=0)
        row = listing(world)[booking.pk]
        assert row['can_report_no_show'] is False
        assert row['report_deadline'] is None

    def test_day_after_check_in_is_reportable_with_deadline(self, world):
        booking = past_stay(world, days_ago_check_in=1)
        row = listing(world)[booking.pk]
        assert row['can_report_no_show'] is True
        assert row['report_deadline'] == str(booking.check_out + timedelta(days=WINDOW))

    def test_last_window_day_is_reportable(self, world):
        booking = stay_ending(world, WINDOW)
        assert listing(world)[booking.pk]['can_report_no_show'] is True

    def test_one_day_after_the_window_is_closed(self, world):
        booking = stay_ending(world, WINDOW + 1)
        row = listing(world)[booking.pk]
        assert row['can_report_no_show'] is False
        assert row['report_deadline'] is None

    @pytest.mark.parametrize('status', ['cancelled', 'no_show', 'pending'])
    def test_other_statuses_are_not_reportable(self, world, status):
        booking = past_stay(world, status=status, paid=False)
        assert listing(world)[booking.pk]['can_report_no_show'] is False

    def test_completed_is_reportable(self, world):
        booking = past_stay(world, days_ago_check_in=3, status='completed')
        assert listing(world)[booking.pk]['can_report_no_show'] is True

    def test_open_report_blocks_and_withdrawn_does_not(self, world):
        booking = past_stay(world)
        report = NoShowReport.objects.create(
            booking=booking, property=booking.property, created_by=world['owner'], comment=COMMENT)
        assert listing(world)[booking.pk]['can_report_no_show'] is False
        NoShowReport.objects.filter(pk=report.pk).update(status='withdrawn')
        assert listing(world)[booking.pk]['can_report_no_show'] is True

    def test_flag_agrees_with_the_report_endpoint(self, world):
        booking = past_stay(world)
        assert listing(world)[booking.pk]['can_report_no_show'] is True
        response = client_for(world['owner']).post(
            f'{P}/bookings/{booking.pk}/no-show-report/', {'comment': COMMENT}, format='json')
        assert response.status_code == 201


@pytest.mark.django_db
class TestReportableFilter:
    def test_filter_keeps_only_reportable_bookings(self, world):
        reportable = past_stay(world, days_ago_check_in=2)
        too_early = past_stay(world, days_ago_check_in=0)
        closed = stay_ending(world, WINDOW + 1)
        rows = listing(world, '?reportable=true')
        assert set(rows) == {reportable.pk}
        assert {reportable.pk, too_early.pk, closed.pk} <= set(listing(world))

    def test_filter_false_or_absent_changes_nothing(self, world):
        past_stay(world, days_ago_check_in=2)
        past_stay(world, days_ago_check_in=0)
        assert len(listing(world, '?reportable=false')) == len(listing(world)) == 2

    def test_filter_ignores_other_owners_bookings(self, world):
        from bookings.tests.r12b_helpers import make_stay as stay
        stay(world['other_prop'], world['guest'], world['today'] - timedelta(days=2),
             room=world['other_room'], rate=world['other_rate'])
        assert listing(world, '?reportable=true') == {}
