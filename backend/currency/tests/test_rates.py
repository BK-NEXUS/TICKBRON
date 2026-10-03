"""
R6: reading the current rate (DB only, never HTTP), staleness, and the
request-level cache used for informational UZS prices.
"""
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

import pytest
from django.test import RequestFactory, override_settings

from currency.models import ExchangeRate
from currency.rates import current_rate, rate_for_request

TODAY = date(2026, 10, 3)


def _seed(rate, day, status='accepted'):
    return ExchangeRate.objects.create(currency='USD', rate=Decimal(rate), nominal=1, rate_date=day,
                                       source='cbu.uz', status=status)


@pytest.mark.django_db
class TestCurrentRate:

    def test_uzs_is_identity_without_lookup(self, django_assert_num_queries):
        with django_assert_num_queries(0):
            info = current_rate('UZS', today=TODAY)
        assert (info.rate, info.source, info.stale) == (Decimal('1'), 'identity', False)

    def test_no_rate_yet_returns_none(self):
        assert current_rate('USD', today=TODAY) is None

    def test_latest_accepted_rate_wins_and_rejected_is_ignored(self):
        _seed('11700', TODAY - timedelta(days=2))
        _seed('11772.95', TODAY - timedelta(days=1))
        _seed('13000', TODAY, status='rejected')
        info = current_rate('USD', today=TODAY)
        assert (info.rate, info.date, info.source, info.stale) == \
            (Decimal('11772.95'), TODAY - timedelta(days=1), 'cbu.uz', False)

    def test_rate_dated_in_the_future_is_not_used_yet(self):
        _seed('11700', TODAY)
        _seed('11800', TODAY + timedelta(days=1))
        assert current_rate('USD', today=TODAY).rate == Decimal('11700')

    def test_stale_after_three_days_still_used_with_warning(self, caplog):
        _seed('11700', TODAY - timedelta(days=4))
        info = current_rate('USD', today=TODAY)
        assert info.rate == Decimal('11700') and info.stale is True
        assert 'stale' in caplog.text

    def test_three_days_old_is_not_stale(self):
        _seed('11700', TODAY - timedelta(days=3))
        assert current_rate('USD', today=TODAY).stale is False

    @override_settings(FX_STALE_AFTER_DAYS=1)
    def test_stale_threshold_is_a_setting(self):
        _seed('11700', TODAY - timedelta(days=2))
        assert current_rate('USD', today=TODAY).stale is True

    def test_never_uses_the_network(self):
        _seed('11700', TODAY)
        with mock.patch('socket.socket', side_effect=AssertionError('network used')):
            assert current_rate('USD', today=TODAY).rate == Decimal('11700')


@pytest.mark.django_db
def test_one_lookup_per_request(django_assert_num_queries):
    from currency.cbu import tashkent_today
    today = tashkent_today()
    _seed('11700', today)
    request = RequestFactory().get('/')
    with django_assert_num_queries(1):
        first = rate_for_request(request, 'USD')
        for _ in range(20):
            assert rate_for_request(request, 'USD') is first
    assert first.date == today
