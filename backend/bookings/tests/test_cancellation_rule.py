"""
R11 free cancellation (.ai/PLAN_R11_CANCELLATION.md): the one rule that decides what a guest gets back
when they cancel a paid booking. A pure function over the terms snapshot stored on the booking.
"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.conf import settings

from bookings.cancellation import free_until, refund_percent_at, terms_for_plan
from bookings.models import Booking
from properties.models import RatePlan

TASHKENT = ZoneInfo('Asia/Tashkent')
CHECK_IN = date(2026, 12, 20)


def terms(free=None, percent=50):
    return Booking(cancel_free_until=free, cancel_refund_percent_after=percent)


class TestFreeUntil:
    def test_none_without_a_free_window(self):
        assert free_until(CHECK_IN, None) is None

    def test_hours_before_the_start_of_the_check_in_day_in_business_time(self):
        assert free_until(CHECK_IN, 48) == datetime(2026, 12, 18, 0, 0, tzinfo=TASHKENT)

    def test_zero_hours_means_until_the_check_in_day_starts(self):
        assert free_until(CHECK_IN, 0) == datetime(2026, 12, 20, 0, 0, tzinfo=TASHKENT)

    def test_is_timezone_aware(self):
        assert free_until(CHECK_IN, 24).tzinfo is not None


class TestRefundPercentAt:
    NOW = datetime(2026, 12, 10, 12, 0, tzinfo=TASHKENT)

    def test_a_booking_without_a_snapshot_promises_nothing(self):
        assert refund_percent_at(terms(percent=None), self.NOW) is None

    def test_inside_the_free_window_everything_comes_back(self):
        assert refund_percent_at(terms(free=self.NOW + timedelta(hours=1)), self.NOW) == 100

    def test_the_last_moment_of_the_window_is_still_free(self):
        assert refund_percent_at(terms(free=self.NOW), self.NOW) == 100

    def test_one_second_later_the_percent_after_applies(self):
        assert refund_percent_at(terms(free=self.NOW - timedelta(seconds=1), percent=50), self.NOW) == 50

    def test_without_a_free_window_the_percent_applies_at_any_time(self):
        assert refund_percent_at(terms(free=None, percent=50), self.NOW) == 50

    @pytest.mark.parametrize('percent', [0, 1, 50, 100])
    def test_the_percent_after_is_used_as_stored(self, percent):
        assert refund_percent_at(terms(percent=percent), self.NOW) == percent

    def test_a_non_refundable_plan_refunds_nothing_even_with_a_free_window_in_the_past(self):
        assert refund_percent_at(terms(free=self.NOW - timedelta(days=1), percent=0), self.NOW) == 0


class TestTermsForPlan:
    def plan(self, hours=None, percent=None):
        return RatePlan(free_cancel_hours=hours, cancel_refund_percent=percent)

    def test_a_plan_with_nothing_set_uses_the_platform_percent_and_has_no_free_window(self):
        assert terms_for_plan(self.plan(), CHECK_IN) == (None, settings.CANCEL_REFUND_PERCENT)

    def test_the_platform_percent_follows_the_setting(self, settings):
        settings.CANCEL_REFUND_PERCENT = 30
        assert terms_for_plan(self.plan(), CHECK_IN) == (None, 30)

    def test_the_owner_can_make_a_plan_non_refundable(self):
        assert terms_for_plan(self.plan(percent=0), CHECK_IN) == (None, 0)

    def test_the_owner_sets_a_free_window_and_a_percent_after_it(self):
        assert terms_for_plan(self.plan(hours=72, percent=25), CHECK_IN) == (
            datetime(2026, 12, 17, 0, 0, tzinfo=TASHKENT), 25)

    def test_a_free_window_alone_keeps_the_platform_percent_after_it(self):
        assert terms_for_plan(self.plan(hours=48), CHECK_IN) == (
            datetime(2026, 12, 18, 0, 0, tzinfo=TASHKENT), settings.CANCEL_REFUND_PERCENT)


def test_the_default_platform_percent_is_fifty():
    # The owner's answer to decision 1: "the refund is 50%"
    assert settings.CANCEL_REFUND_PERCENT == 50
