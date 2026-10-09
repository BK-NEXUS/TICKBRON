"""Nightly tidy-up: expired promotions end, paid ones that started become active (00:10 Asia/Tashkent)."""
from datetime import date, datetime, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.conf import settings
from django.utils import timezone

from promotions import service
from promotions.models import Promotion
from promotions.tasks import end_expired_promotions
from promotions.tests.helpers import make_hotel, make_owner

pytestmark = pytest.mark.django_db
LAST_DAY = date(2026, 10, 9)


def at(hour_utc, day=9):
    return patch('common.dates.timezone.now', return_value=datetime(2026, 10, day, hour_utc, 30, tzinfo=dt_timezone.utc))


def make(email, start, end, status, paid=True):
    prop = make_hotel(make_owner(email), name=email)
    return Promotion.objects.create(
        property=prop, start_date=start, end_date=end, status=status, price_amount=Decimal('1'),
        paid_at=timezone.now() if paid else None)


def reload(promotion):
    promotion.refresh_from_db()
    return promotion.status


def test_beat_entry_runs_at_0010_tashkent():
    entry = settings.CELERY_BEAT_SCHEDULE['end-expired-promotions']
    assert entry['task'] == 'promotions.tasks.end_expired_promotions'
    assert (entry['schedule'].hour, entry['schedule'].minute) == ({0}, {10})
    assert settings.CELERY_TIMEZONE == 'Asia/Tashkent'


def test_last_day_is_still_running_at_2330_tashkent():
    promo = make('a@example.com', date(2026, 10, 3), LAST_DAY, 'active')
    with at(18):  # 23:30 on 9 Oct in Tashkent
        result = end_expired_promotions()
        assert reload(promo) == 'active'
        assert list(service.shown_now()) == [promo]
    assert result == {'ended': 0, 'activated': 0}


def test_it_ends_after_midnight_tashkent():
    promo = make('b@example.com', date(2026, 10, 3), LAST_DAY, 'active')
    with at(19):  # 00:30 on 10 Oct in Tashkent (19:30 UTC on the 9th)
        result = end_expired_promotions()
        assert list(service.shown_now()) == []
    assert reload(promo) == 'ended'
    assert result['ended'] == 1


def test_serving_does_not_wait_for_the_task():
    promo = make('c@example.com', date(2026, 10, 3), LAST_DAY, 'active')
    with at(19):
        assert list(service.shown_now()) == []
    assert reload(promo) == 'active'


def test_paid_scheduled_promotion_that_started_becomes_active():
    promo = make('d@example.com', date(2026, 10, 9), date(2026, 10, 20), 'scheduled')
    with at(19, day=9):
        end_expired_promotions()
    assert reload(promo) == 'active'


def test_unpaid_or_future_scheduled_stay_scheduled():
    unpaid = make('e@example.com', date(2026, 10, 1), date(2026, 10, 20), 'scheduled', paid=False)
    future = make('f@example.com', date(2026, 10, 15), date(2026, 10, 20), 'scheduled')
    with at(10):
        end_expired_promotions()
    assert (reload(unpaid), reload(future)) == ('scheduled', 'scheduled')


def test_paused_expired_promotion_ends_too():
    promo = make('g@example.com', date(2026, 10, 1), date(2026, 10, 5), 'paused')
    with at(10):
        end_expired_promotions()
    assert reload(promo) == 'ended'


def test_cancelled_and_ended_are_left_alone():
    cancelled = make('h@example.com', date(2026, 10, 1), date(2026, 10, 5), 'cancelled')
    ended = make('i@example.com', date(2026, 9, 1), date(2026, 9, 5), 'ended')
    with at(10):
        result = end_expired_promotions()
    assert (reload(cancelled), reload(ended)) == ('cancelled', 'ended')
    assert result == {'ended': 0, 'activated': 0}


def test_paused_promotion_inside_its_dates_is_not_activated():
    promo = make('j@example.com', date(2026, 10, 1), date(2026, 10, 20), 'paused')
    with at(10):
        end_expired_promotions()
    assert reload(promo) == 'paused'


def test_deleted_promotions_are_ignored_and_task_is_idempotent():
    gone = make('k@example.com', date(2026, 10, 1), date(2026, 10, 5), 'active')
    gone.soft_delete()
    live = make('l@example.com', date(2026, 10, 1), date(2026, 10, 5), 'active')
    with at(10):
        assert end_expired_promotions()['ended'] == 1
        assert end_expired_promotions() == {'ended': 0, 'activated': 0}
    assert reload(live) == 'ended'
    assert reload(gone) == 'active'
