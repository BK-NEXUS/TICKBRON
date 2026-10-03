"""
R6: the CBU rate fetch. Runs only in the Celery task / management command, with
mocked HTTP here. A bad answer never replaces the last good rate.
"""
import json
import urllib.error
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from unittest import mock

import pytest
from django.core.management import call_command
from django.test import override_settings

from currency import cbu
from currency.models import ExchangeRate, ExchangeRateFetch

TODAY = date(2026, 10, 3)


def _body(rate='11772.95', nominal='1', day='03.10.2026', ccy='USD', code='840', extra=None):
    item = {'id': 1, 'Code': code, 'Ccy': ccy, 'CcyNm_EN': 'US Dollar', 'Nominal': nominal,
            'Rate': rate, 'Diff': '-35.81', 'Date': day}
    return json.dumps([item] + (extra or [])).encode()


class FakeResponse:
    def __init__(self, body, status=200, content_type='application/json'):
        self.status = status
        self.headers = {'Content-Type': content_type}
        self._body = BytesIO(body)

    def read(self, size=-1):
        return self._body.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _serve(*responses):
    """Patch the opener: each call returns the next response (or raises it)."""
    calls = []

    def fake_open(request, timeout):
        calls.append((request.full_url, timeout))
        item = responses[min(len(calls), len(responses)) - 1]
        if isinstance(item, Exception):
            raise item
        return item
    return mock.patch.object(cbu._OPENER, 'open', side_effect=fake_open), calls


def _accepted():
    return list(ExchangeRate.objects.filter(status='accepted').values_list('rate', 'rate_date'))


def _seed(rate, day):
    return ExchangeRate.objects.create(currency='USD', rate=Decimal(rate), nominal=1, rate_date=day,
                                       source='cbu.uz', status='accepted')


@pytest.mark.django_db
class TestSuccess:

    def test_fixed_url_timeout_and_parsed_strings(self):
        patcher, calls = _serve(FakeResponse(_body()))
        with patcher:
            cbu.fetch_and_store(today=TODAY)

        assert calls == [('https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/2026-10-03/', 10)]
        assert _accepted() == [(Decimal('11772.950000'), TODAY)]
        row = ExchangeRate.objects.get()
        assert (row.source, row.nominal) == ('cbu.uz', 1)
        assert ExchangeRateFetch.objects.get().success is True

    def test_nominal_divides_the_rate(self):
        patcher, _ = _serve(FakeResponse(_body(rate='117729.50', nominal='10')))
        with patcher:
            cbu.fetch_and_store(today=TODAY)
        assert _accepted() == [(Decimal('11772.950000'), TODAY)]

    def test_date_comes_from_the_body_not_the_url(self):
        patcher, _ = _serve(FakeResponse(_body(day='02.10.2026')))
        with patcher:
            cbu.fetch_and_store(today=TODAY)
        assert _accepted() == [(Decimal('11772.950000'), date(2026, 10, 2))]

    def test_same_date_twice_is_stored_once(self):
        patcher, _ = _serve(FakeResponse(_body()), FakeResponse(_body()))
        with patcher:
            cbu.fetch_and_store(today=TODAY)
            cbu.fetch_and_store(today=TODAY)
        assert ExchangeRate.objects.count() == 1


@pytest.mark.django_db
class TestFailuresKeepTheOldRate:

    @pytest.mark.parametrize('response', [
        urllib.error.URLError('timed out'),
        TimeoutError('timed out'),
        FakeResponse(b'oops', status=500),
        FakeResponse(b'<html>maintenance</html>', content_type='text/html'),
        FakeResponse(b'not json'),
        FakeResponse(b'[]'),
        FakeResponse(_body(extra=[{'Ccy': 'EUR'}])),
        FakeResponse(_body(ccy='EUR', code='978')),
        FakeResponse(_body(rate='abc')),
        FakeResponse(_body(rate='-5')),
        FakeResponse(_body(nominal='0')),
        FakeResponse(_body(day='2026-10-03')),
        FakeResponse(_body(day='04.10.2026')),        # in the future
        FakeResponse(_body(day='20.09.2026')),        # older than 10 days
        FakeResponse(b'[' + b' ' * 70000 + b']'),     # over the 64 KB cap
    ])
    def test_bad_answer(self, response, caplog):
        _seed('11700.00', TODAY - timedelta(days=1))
        patcher, _ = _serve(response)
        with patcher:
            cbu.fetch_and_store(today=TODAY)

        assert _accepted() == [(Decimal('11700.000000'), TODAY - timedelta(days=1))]
        fetch = ExchangeRateFetch.objects.get()
        assert fetch.success is False and fetch.error
        assert 'USD' in caplog.text

    def test_redirects_are_refused(self):
        handler = cbu._NoRedirect()
        with pytest.raises(cbu.FetchError):
            handler.redirect_request(mock.Mock(), None, 302, 'Found', {}, 'https://evil.example/json')

    def test_opener_has_no_default_redirect_handler(self):
        import urllib.request
        handlers = cbu._OPENER.handlers
        assert any(isinstance(h, cbu._NoRedirect) for h in handlers)
        assert not any(type(h) is urllib.request.HTTPRedirectHandler for h in handlers)


@pytest.mark.django_db
class TestSanityChecks:

    def test_jump_over_threshold_is_stored_as_rejected_and_not_used(self, caplog):
        _seed('11700.00', TODAY - timedelta(days=1))
        patcher, _ = _serve(FakeResponse(_body(rate='13000.00')))   # +11.1 %
        with patcher:
            cbu.fetch_and_store(today=TODAY)

        assert _accepted() == [(Decimal('11700.000000'), TODAY - timedelta(days=1))]
        rejected = ExchangeRate.objects.get(status='rejected')
        assert rejected.rate == Decimal('13000') and 'change' in rejected.note
        assert 'rejected' in caplog.text

    def test_jump_within_threshold_is_accepted(self):
        _seed('11700.00', TODAY - timedelta(days=1))
        patcher, _ = _serve(FakeResponse(_body(rate='12800.00')))   # +9.4 %
        with patcher:
            cbu.fetch_and_store(today=TODAY)
        assert (Decimal('12800.000000'), TODAY) in _accepted()

    @pytest.mark.parametrize('rate', ['999.99', '100000.01'])
    def test_absurd_values_are_rejected_even_without_history(self, rate):
        patcher, _ = _serve(FakeResponse(_body(rate=rate)))
        with patcher:
            cbu.fetch_and_store(today=TODAY)
        assert _accepted() == []
        assert ExchangeRate.objects.get().status == 'rejected'

    @override_settings(FX_MAX_CHANGE=Decimal('0.20'), FX_MIN_RATE=Decimal('5000'), FX_MAX_RATE=Decimal('50000'))
    def test_thresholds_come_from_settings(self):
        _seed('11700.00', TODAY - timedelta(days=1))
        patcher, _ = _serve(FakeResponse(_body(rate='13000.00')))
        with patcher:
            cbu.fetch_and_store(today=TODAY)
        assert (Decimal('13000.000000'), TODAY) in _accepted()


@pytest.mark.django_db
def test_management_command_runs_the_same_fetch():
    patcher, calls = _serve(FakeResponse(_body()))
    with patcher, mock.patch('currency.cbu.tashkent_today', return_value=TODAY):
        call_command('fetch_exchange_rates')
    assert len(calls) == 1 and _accepted()


def test_beat_schedule_runs_the_task_twice_a_day():
    from django.conf import settings
    entry = settings.CELERY_BEAT_SCHEDULE['fetch-exchange-rates']
    assert entry['task'] == 'currency.tasks.fetch_exchange_rates'
    assert entry['schedule'].hour == {4, 13}       # 09:00 and 18:00 Asia/Tashkent (UTC+5)


def test_settings_defaults_and_environment():
    from core.tests.test_settings_defaults import _load_settings
    defaults = _load_settings('settings.FX_STALE_AFTER_DAYS, settings.FX_MAX_CHANGE, '
                              'settings.FX_MIN_RATE, settings.FX_MAX_RATE')
    assert defaults == '3 0.10 1000 100000'
    custom = _load_settings('settings.FX_STALE_AFTER_DAYS, settings.FX_MAX_CHANGE', FX_STALE_AFTER_DAYS='5',
                            FX_MAX_CHANGE='0.05')
    assert custom == '5 0.05'
