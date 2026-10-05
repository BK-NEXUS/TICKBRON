"""
R6: staff see the rate history; super-admins see the rate status (for the frontend's
warning banner) and may accept a rate the fetch rejected for jumping too far. Every
accept is written to the admin audit log: who, old rate, new rate, when.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from currency.cbu import tashkent_today
from currency.models import ExchangeRate, ExchangeRateFetch
from currency.rates import current_rate
from users.models import User

# R6: these tests control the exchange rates themselves (no rate, stale, fetch, accept)
pytestmark = pytest.mark.no_default_exchange_rate

A = '/api/v1/admin-panel/exchange-rates'


def _client(user):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


@pytest.fixture
def people(db):
    return {
        'guest': User.objects.create_user(email='g@example.com', password='x'),
        'staff': User.objects.create_user(email='s@example.com', password='x', is_staff=True),
        'super': User.objects.create_user(email='a@example.com', password='x', is_staff=True, is_superuser=True),
    }


@pytest.fixture
def rates(db):
    today = tashkent_today()
    old = ExchangeRate.objects.create(currency='USD', rate=Decimal('11772.95'), nominal=1, source='cbu.uz',
                                      status='accepted', rate_date=today - timedelta(days=1))
    jump = ExchangeRate.objects.create(currency='USD', rate=Decimal('13500'), nominal=1, source='cbu.uz',
                                       status='rejected', rate_date=today,
                                       note='rejected: change of 14.7% from 11772.950000 exceeds 10%')
    ExchangeRateFetch.objects.create(currency='USD', success=False, exchange_rate=jump, error=jump.note)
    return {'old': old, 'jump': jump, 'today': today}


@pytest.mark.django_db
class TestRateStatus:

    def test_super_admin_sees_latest_rate_staleness_and_last_error(self, people, rates):
        response = _client(people['super']).get(f'{A}/status/')

        assert response.status_code == 200
        usd = response.data['currencies'][0]
        assert usd['currency'] == 'USD'
        assert usd['rate'] == '11772.950000'
        assert usd['date'] == (rates['today'] - timedelta(days=1)).isoformat()
        assert usd['stale'] is False
        assert usd['last_fetch']['success'] is False
        assert usd['last_error'] == rates['jump'].note
        assert [r['id'] for r in usd['rejected']] == [rates['jump'].id]

    def test_no_rate_at_all(self, people, db):
        usd = _client(people['super']).get(f'{A}/status/').data['currencies'][0]
        assert (usd['rate'], usd['date'], usd['stale'], usd['last_fetch'], usd['last_error']) == \
            (None, None, True, None, None)

    def test_stale_rate(self, people, db):
        ExchangeRate.objects.create(currency='USD', rate=Decimal('11772.95'), nominal=1, source='cbu.uz',
                                    status='accepted', rate_date=tashkent_today() - timedelta(days=4))
        assert _client(people['super']).get(f'{A}/status/').data['currencies'][0]['stale'] is True

    @pytest.mark.parametrize('who, code', [(None, 403), ('guest', 403), ('staff', 403)])
    def test_only_super_admin(self, people, rates, who, code):
        response = _client(people.get(who)).get(f'{A}/status/')
        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestRateHistory:

    def test_staff_can_read_history(self, people, rates):
        response = _client(people['staff']).get(f'{A}/')
        assert response.status_code == 200
        assert [r['status'] for r in response.data['results']] == ['rejected', 'accepted']

    def test_guest_cannot(self, people, rates):
        assert _client(people['guest']).get(f'{A}/').status_code == 403


@pytest.mark.django_db
class TestAcceptRejectedRate:

    def test_super_admin_accepts_and_it_becomes_current_and_audited(self, people, rates):
        assert current_rate('USD').rate == Decimal('11772.95')

        response = _client(people['super']).post(f"{A}/{rates['jump'].id}/accept/")

        assert response.status_code == 201, response.data
        assert current_rate('USD').rate == Decimal('13500')
        # the rejected row itself is history and stays as it was
        assert ExchangeRate.objects.get(pk=rates['jump'].id).status == 'rejected'
        entry = AdminAccessLog.objects.get(action='exchange_rate_accept')
        assert entry.actor_id == people['super'].id
        assert entry.details == {
            'currency': 'USD', 'rate_date': rates['today'].isoformat(),
            'old_rate': '11772.950000', 'new_rate': '13500.000000',
            'rejected_id': rates['jump'].id, 'accepted_id': response.data['id'],
        }
        assert entry.created_at is not None

    @pytest.mark.parametrize('who', [None, 'guest', 'staff'])
    def test_others_cannot_accept(self, people, rates, who):
        response = _client(people.get(who)).post(f"{A}/{rates['jump'].id}/accept/")

        assert response.status_code in (401, 403)
        assert current_rate('USD').rate == Decimal('11772.95')
        assert not AdminAccessLog.objects.filter(action='exchange_rate_accept').exists()

    def test_accepted_row_cannot_be_accepted_again(self, people, rates):
        response = _client(people['super']).post(f"{A}/{rates['old'].id}/accept/")
        assert response.status_code == 400

    def test_second_accept_of_the_same_day_is_refused(self, people, rates):
        assert _client(people['super']).post(f"{A}/{rates['jump'].id}/accept/").status_code == 201
        response = _client(people['super']).post(f"{A}/{rates['jump'].id}/accept/")
        assert response.status_code == 409
        assert ExchangeRate.objects.filter(status='accepted', rate_date=rates['today']).count() == 1

    def test_unknown_id(self, people, db):
        assert _client(people['super']).post(f'{A}/999999/accept/').status_code == 404
