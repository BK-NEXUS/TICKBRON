"""Kirisiw session ları database degi qatarlar. Django múddeti ótkenlerin ózi óshirmeydi, sol sebepli túngi task óshiredi."""
from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.sessions.models import Session
from django.utils import timezone

from common.tasks import clear_expired_sessions

pytestmark = pytest.mark.django_db


def make_session(key, expires_in):
    return Session.objects.create(session_key=key, session_data='x', expire_date=timezone.now() + expires_in)


def test_the_task_removes_expired_sessions_and_keeps_live_ones():
    make_session('live', timedelta(days=1))
    make_session('expired', timedelta(days=-1))
    clear_expired_sessions()
    assert list(Session.objects.values_list('session_key', flat=True)) == ['live']


def test_the_task_runs_once_every_night():
    entries = [entry for entry in settings.CELERY_BEAT_SCHEDULE.values() if entry['task'] == 'common.tasks.clear_expired_sessions']
    assert len(entries) == 1
    assert entries[0]['schedule'].hour == {3} and entries[0]['schedule'].minute == {30}
