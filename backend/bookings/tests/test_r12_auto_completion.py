"""
R12 1b: confirmed bookings whose check-out date is before the business date become
`completed`, every night at 00:05 Asia/Tashkent and by a one-off command. A missed
run heals itself (check_out < today, not "== yesterday"). Every real run is recorded
(time, number changed) and shown to super-admins.
"""
from datetime import datetime, timedelta, timezone as dt_timezone
from io import StringIO
from unittest import mock

import pytest
from django.conf import settings
from django.core.management import call_command
from rest_framework.test import APIClient

from bookings.completion import CompletionError, complete_finished_stays
from bookings.models import AutoCompletionRun, Booking
from bookings.tests.r12_helpers import at_tashkent, make_booking
from common.dates import business_today
from payments.models import PaymentAuditLog
from properties.models import Property, PropertyType
from users.models import User

URL = '/api/v1/admin-panel/auto-completion/status/'


@pytest.fixture
def hotel(db):
    owner = User.objects.create_user(email='owner@example.com', password='x')
    return Property.objects.create(
        owner=owner, property_type=PropertyType.objects.create(name='Hotel', slug='hotel'),
        status='active', max_guests=2, bedrooms=1, bathrooms=1, address_line1='1 Main',
        city='Tashkent', country='Uzbekistan', base_price=500000, currency='UZS',
    )


@pytest.fixture
def guest(db):
    return User.objects.create_user(email='guest@example.com', password='x')


def _status(booking):
    return Booking.objects.get(pk=booking.pk).status


@pytest.mark.django_db
class TestCompletion:

    def test_only_confirmed_stays_that_ended_before_today_complete(self, hotel, guest):
        today = business_today()
        ended = make_booking(hotel, guest, today - timedelta(days=3), nights=2)          # out yesterday
        leaving_today = make_booking(hotel, guest, today - timedelta(days=2), nights=2)  # out today
        future = make_booking(hotel, guest, today + timedelta(days=5))
        others = [make_booking(hotel, guest, today - timedelta(days=9), status=s)
                  for s in ('pending', 'cancelled', 'no_show', 'completed')]

        result = complete_finished_stays()

        assert result == {'eligible': 1, 'changed': 1, 'failed': 0}
        assert _status(ended) == 'completed'
        assert _status(leaving_today) == 'confirmed'
        assert _status(future) == 'confirmed'
        assert [_status(b) for b in others] == ['pending', 'cancelled', 'no_show', 'completed']

    def test_missed_runs_heal_themselves(self, hotel, guest):
        today = business_today()
        old = [make_booking(hotel, guest, today - timedelta(days=d), nights=1) for d in (2, 5, 40)]
        assert complete_finished_stays()['changed'] == 3
        assert {_status(b) for b in old} == {'completed'}

    def test_second_run_changes_nothing(self, hotel, guest):
        make_booking(hotel, guest, business_today() - timedelta(days=4))
        assert complete_finished_stays()['changed'] == 1
        assert complete_finished_stays() == {'eligible': 0, 'changed': 0, 'failed': 0}

    def test_state_change_is_audit_logged(self, hotel, guest):
        booking = make_booking(hotel, guest, business_today() - timedelta(days=4))
        complete_finished_stays()
        log = PaymentAuditLog.objects.get(booking=booking, action='booking_status_changed')
        assert (log.old_status, log.new_status, log.details['reason']) == ('confirmed', 'completed',
                                                                            'checkout_completed')

    def test_run_is_recorded_with_time_and_count(self, hotel, guest):
        make_booking(hotel, guest, business_today() - timedelta(days=4))
        make_booking(hotel, guest, business_today() - timedelta(days=6))
        complete_finished_stays(trigger='beat')
        run = AutoCompletionRun.objects.get()
        assert (run.changed, run.failed, run.trigger) == (2, 0, 'beat')
        assert run.started_at <= run.finished_at

    def test_dry_run_changes_and_records_nothing(self, hotel, guest):
        booking = make_booking(hotel, guest, business_today() - timedelta(days=4))
        assert complete_finished_stays(dry_run=True) == {'eligible': 1, 'changed': 0, 'failed': 0}
        assert _status(booking) == 'confirmed'
        assert not AutoCompletionRun.objects.exists()

    def test_one_failure_does_not_stop_the_others_and_is_counted(self, hotel, guest):
        first = make_booking(hotel, guest, business_today() - timedelta(days=4))
        second = make_booking(hotel, guest, business_today() - timedelta(days=5))
        real = Booking.complete_booking

        def flaky(self):
            if self.pk == first.pk:
                raise RuntimeError('boom')
            return real(self)

        with mock.patch.object(Booking, 'complete_booking', flaky):
            result = complete_finished_stays()
        assert result == {'eligible': 2, 'changed': 1, 'failed': 1}
        assert (_status(first), _status(second)) == ('confirmed', 'completed')
        assert AutoCompletionRun.objects.get().failed == 1

    def test_task_raises_after_processing_when_something_failed(self, hotel, guest):
        from bookings.tasks import complete_finished_stays as task
        make_booking(hotel, guest, business_today() - timedelta(days=4))
        with mock.patch.object(Booking, 'complete_booking', side_effect=RuntimeError('boom')):
            with pytest.raises(CompletionError):
                task()
        assert AutoCompletionRun.objects.get().trigger == 'beat'

    def test_business_date_decides_at_half_past_midnight_tashkent(self, hotel, guest):
        # 00:30 Tashkent on D+1 is 19:30 UTC on D. Check-out on D has passed in Tashkent.
        day = business_today() + timedelta(days=30)
        booking = make_booking(hotel, guest, day - timedelta(days=2), nights=2)   # check-out D
        with at_tashkent(day + timedelta(days=1), 0, 30):
            assert complete_finished_stays()['changed'] == 1
        assert _status(booking) == 'completed'

    def test_at_half_past_eleven_the_same_day_is_not_over(self, hotel, guest):
        day = business_today() + timedelta(days=30)
        booking = make_booking(hotel, guest, day - timedelta(days=2), nights=2)   # check-out D
        with at_tashkent(day, 23, 30):
            assert complete_finished_stays()['changed'] == 0
        assert _status(booking) == 'confirmed'


@pytest.mark.django_db
class TestCommand:

    def test_dry_run_prints_counts_and_changes_nothing(self, hotel, guest):
        booking = make_booking(hotel, guest, business_today() - timedelta(days=4))
        out = StringIO()
        call_command('complete_finished_stays', '--dry-run', stdout=out)
        assert 'eligible: 1' in out.getvalue()
        assert 'dry run' in out.getvalue().lower()
        assert _status(booking) == 'confirmed'
        assert not AutoCompletionRun.objects.exists()

    def test_real_run_prints_counts_before_changing(self, hotel, guest):
        booking = make_booking(hotel, guest, business_today() - timedelta(days=4))
        out = StringIO()
        call_command('complete_finished_stays', stdout=out)
        text = out.getvalue()
        assert text.index('eligible: 1') < text.index('changed: 1')
        assert _status(booking) == 'completed'
        assert AutoCompletionRun.objects.get().trigger == 'command'


class TestSchedule:

    def test_celery_runs_in_the_business_time_zone(self):
        assert settings.CELERY_TIMEZONE == settings.BUSINESS_TIME_ZONE == 'Asia/Tashkent'
        assert settings.TIME_ZONE == 'UTC'

    def _next_run_utc(self, entry_name, now_utc, last_run_utc):
        from config.celery import app
        schedule = settings.CELERY_BEAT_SCHEDULE[entry_name]['schedule']
        bound = type(schedule)(minute=schedule._orig_minute, hour=schedule._orig_hour,
                               app=app, nowfun=lambda: now_utc.astimezone(app.timezone))
        return now_utc + bound.remaining_estimate(last_run_utc.astimezone(app.timezone))

    def test_completion_fires_at_0005_tashkent(self):
        entry = settings.CELERY_BEAT_SCHEDULE['complete-finished-stays']
        assert entry['task'] == 'bookings.tasks.complete_finished_stays'
        # Monday 23:00 Tashkent (18:00 UTC), last run at 00:05 that morning
        now = datetime(2026, 10, 5, 18, 0, tzinfo=dt_timezone.utc)
        last = datetime(2026, 10, 4, 19, 5, tzinfo=dt_timezone.utc)
        assert self._next_run_utc('complete-finished-stays', now, last) == datetime(
            2026, 10, 5, 19, 5, tzinfo=dt_timezone.utc)   # = 00:05 on 6 October in Tashkent

    def test_exchange_rate_fetch_keeps_its_real_times(self):
        # 09:00 and 18:00 Tashkent = 04:00 and 13:00 UTC, unchanged by the Celery time zone move
        now = datetime(2026, 10, 5, 3, 0, tzinfo=dt_timezone.utc)
        last = datetime(2026, 10, 4, 13, 0, tzinfo=dt_timezone.utc)
        assert self._next_run_utc('fetch-exchange-rates', now, last) == datetime(
            2026, 10, 5, 4, 0, tzinfo=dt_timezone.utc)
        now = datetime(2026, 10, 5, 5, 0, tzinfo=dt_timezone.utc)
        last = datetime(2026, 10, 5, 4, 0, tzinfo=dt_timezone.utc)
        assert self._next_run_utc('fetch-exchange-rates', now, last) == datetime(
            2026, 10, 5, 13, 0, tzinfo=dt_timezone.utc)


@pytest.mark.django_db
class TestStatusEndpoint:

    @pytest.fixture
    def people(self, db):
        return {
            'guest': User.objects.create_user(email='g@example.com', password='x'),
            'staff': User.objects.create_user(email='s@example.com', password='x', is_staff=True),
            'super': User.objects.create_user(email='a@example.com', password='x', is_staff=True,
                                              is_superuser=True),
        }

    def _get(self, user):
        client = APIClient()
        if user:
            client.force_authenticate(user=user)
        return client.get(URL)

    def test_super_admin_sees_last_run_and_waiting_count(self, people, hotel, guest):
        make_booking(hotel, guest, business_today() - timedelta(days=4))
        complete_finished_stays(trigger='beat')
        make_booking(hotel, guest, business_today() - timedelta(days=5))   # arrived after the run

        response = self._get(people['super'])

        assert response.status_code == 200
        assert response.data['last_run']['changed'] == 1
        assert response.data['last_run']['failed'] == 0
        assert response.data['last_run']['trigger'] == 'beat'
        assert response.data['last_run']['finished_at']
        assert response.data['waiting'] == 1
        assert response.data['schedule'] == '00:05 Asia/Tashkent'

    def test_no_run_yet(self, people):
        response = self._get(people['super'])
        assert response.status_code == 200
        assert response.data['last_run'] is None
        assert response.data['waiting'] == 0

    @pytest.mark.parametrize('who, code', [(None, (401, 403)), ('guest', (403,)), ('staff', (403,))])
    def test_only_super_admin(self, people, who, code):
        assert self._get(people[who] if who else None).status_code in code
