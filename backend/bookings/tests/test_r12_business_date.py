"""
R12 1a: booking create, quote and availability reject a check-in before the BUSINESS
date (Asia/Tashkent), not the UTC date. Between 00:00 and 05:00 in Tashkent the UTC
date is still yesterday; a check-in for "yesterday" must be refused then.
"""
from datetime import datetime, time, timedelta, timezone as dt_timezone
from unittest import mock
import zoneinfo

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from bookings.models import Booking
from bookings.tests.test_quote import stay  # noqa: F401  (fixture: property, nights from start)
from bookings.tests.test_r6_snapshot import _make_uzs

TASHKENT = zoneinfo.ZoneInfo('Asia/Tashkent')


def _tashkent(day, hour, minute):
    """Patch "now" to the given local Tashkent time (stored and compared in UTC)."""
    moment = datetime.combine(day, time(hour, minute), tzinfo=TASHKENT).astimezone(dt_timezone.utc)
    return mock.patch('django.utils.timezone.now', return_value=moment)


def _book(stay, check_in, nights=2):
    client = APIClient()
    client.force_authenticate(user=stay['guest'])
    return client.post('/api/v1/bookings/', {
        'property_id': stay['property'].id, 'room_type_id': stay['room'].id, 'rate_plan_id': stay['rate'].id,
        'check_in': check_in.isoformat(), 'check_out': (check_in + timedelta(days=nights)).isoformat(),
        'guest_count': 1,
    }, format='json')


def _quote(stay, check_in):
    return APIClient().get(f"/api/v1/properties/{stay['property'].id}/quote/", {
        'room_type_id': stay['room'].id, 'rate_plan_id': stay['rate'].id,
        'check_in': check_in.isoformat(), 'check_out': (check_in + timedelta(days=1)).isoformat(),
    })


def _availability(stay, check_in):
    return APIClient().get(f"/api/v1/properties/{stay['property'].id}/availability/", {
        'check_in': check_in.isoformat(), 'check_out': (check_in + timedelta(days=1)).isoformat(),
    })


@pytest.mark.django_db
class TestAtHalfPastMidnightTashkent:
    """00:30 in Tashkent on day D+1 = 19:30 UTC on day D: the UTC date is D, the business date D+1."""

    @pytest.fixture
    def day(self, stay):
        _make_uzs(stay)
        return stay['start'] + timedelta(days=1)   # business today

    def test_api_refuses_check_in_on_the_business_yesterday(self, stay, day):
        with _tashkent(day, 0, 30):
            response = _book(stay, day - timedelta(days=1))
        assert response.status_code == 400, response.data
        assert 'check_in' in str(response.data)
        assert not Booking.objects.exists()

    def test_api_accepts_check_in_on_the_business_today(self, stay, day):
        with _tashkent(day, 0, 30):
            response = _book(stay, day)
        assert response.status_code == 201, response.data

    def test_model_refuses_check_in_on_the_business_yesterday(self, stay, day):
        with _tashkent(day, 0, 30), pytest.raises(ValidationError) as error:
            Booking.create_booking(
                guest=stay['guest'], property_obj=stay['property'], room_type=stay['room'],
                rate_plan=stay['rate'], check_in=day - timedelta(days=1), check_out=day + timedelta(days=1),
                guest_count=1,
            )
        assert 'check_in' in error.value.message_dict

    def test_quote_refuses_the_business_yesterday(self, stay, day):
        with _tashkent(day, 0, 30):
            assert _quote(stay, day - timedelta(days=1)).status_code == 400
            assert _quote(stay, day).status_code == 200

    def test_availability_refuses_the_business_yesterday(self, stay, day):
        with _tashkent(day, 0, 30):
            assert _availability(stay, day - timedelta(days=1)).status_code == 400
            assert _availability(stay, day).status_code == 200


@pytest.mark.django_db
class TestAtHalfPastElevenTashkent:
    """23:30 in Tashkent on day D = 18:30 UTC on day D: both dates are D."""

    @pytest.fixture
    def day(self, stay):
        _make_uzs(stay)
        return stay['start'] + timedelta(days=1)

    def test_check_in_today_is_accepted(self, stay, day):
        with _tashkent(day, 23, 30):
            response = _book(stay, day)
        assert response.status_code == 201, response.data

    def test_check_in_yesterday_is_refused(self, stay, day):
        with _tashkent(day, 23, 30):
            response = _book(stay, day - timedelta(days=1))
        assert response.status_code == 400
