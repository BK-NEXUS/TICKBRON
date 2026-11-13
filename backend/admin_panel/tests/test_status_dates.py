"""
QA tabılması F12: status endpoint leri sanalar period=custom siz jiberilgende ádetdegi dáwir menen 200 menen juwap berdi,
sol sebepli jazıwdaǵı qátelik nátiyjedey kórindi. Endi ol 400.
"""
import pytest
from rest_framework.test import APIClient

from users.models import User

OVERVIEW = '/api/v1/admin-panel/status/overview/'


@pytest.fixture
def staff(db):
    return User.objects.create_user(email='staff@example.com', password='x', is_staff=True)


def get(staff, query):
    client = APIClient()
    client.force_authenticate(user=staff)
    return client.get(f'{OVERVIEW}?{query}')


@pytest.mark.django_db
class TestStatusDates:
    @pytest.mark.parametrize('query', [
        'from=2026-05-01&to=2026-04-01',
        'from=x',
        'to=2026-04-01',
        'period=last_7_days&from=2026-04-01&to=2026-04-30',
        'period=custom&from=x&to=2026-04-30',
        'period=custom&from=2026-05-01&to=2026-04-01',
        'period=custom&from=2026-04-01',
    ])
    def test_bad_or_misplaced_dates_are_a_400(self, staff, query):
        response = get(staff, query)
        assert response.status_code == 400, response.data

    @pytest.mark.parametrize('query', [
        '',
        'period=last_30_days',
        'period=custom&from=2026-04-01&to=2026-04-30',
        'period=2026-04',
    ])
    def test_good_requests_still_work(self, staff, query):
        assert get(staff, query).status_code == 200
