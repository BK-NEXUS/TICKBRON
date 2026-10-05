"""
R12 1a: the business date. TIME_ZONE stays UTC; "today" for bookings, statistics and
auto-completion is the date in BUSINESS_TIME_ZONE (default Asia/Tashkent, UTC+5).
"""
from datetime import date, datetime, timezone as dt_timezone
from unittest import mock

from django.test import override_settings

from common.dates import business_today


def _at_utc(*args):
    return mock.patch('django.utils.timezone.now', return_value=datetime(*args, tzinfo=dt_timezone.utc))


def test_default_business_time_zone_is_tashkent(settings):
    assert settings.BUSINESS_TIME_ZONE == 'Asia/Tashkent'
    assert settings.TIME_ZONE == 'UTC'


def test_0030_tashkent_is_already_the_next_day():
    with _at_utc(2026, 10, 5, 19, 30):   # 00:30 on 6 October in Tashkent
        assert business_today() == date(2026, 10, 6)


def test_2330_tashkent_is_still_the_same_day():
    with _at_utc(2026, 10, 5, 18, 30):   # 23:30 on 5 October in Tashkent
        assert business_today() == date(2026, 10, 5)


def test_boundary_is_tashkent_midnight():
    with _at_utc(2026, 10, 5, 18, 59, 59):
        assert business_today() == date(2026, 10, 5)
    with _at_utc(2026, 10, 5, 19, 0, 0):
        assert business_today() == date(2026, 10, 6)


@override_settings(BUSINESS_TIME_ZONE='UTC')
def test_setting_changes_the_business_date():
    with _at_utc(2026, 10, 5, 19, 30):
        assert business_today() == date(2026, 10, 5)


def test_cbu_rate_date_uses_the_same_helper():
    from currency.cbu import tashkent_today
    with _at_utc(2026, 10, 5, 19, 30):
        assert tashkent_today() == date(2026, 10, 6)
