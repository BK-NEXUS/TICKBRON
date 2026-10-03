"""
R4 security review: a stay is at most MAX_STAY_NIGHTS nights.

A rate plan may leave max_nights empty ("unlimited"). quote_stay then built a list
of every night up to check_out, so one anonymous GET /quote/ with check_out in the
year 9999 made the server build ~2.9 million dates and send them in one SQL IN
list; a booking request with lock=True also created a RoomInventory row for every
missing night before checking availability.
"""
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from bookings.pricing import MAX_STAY_NIGHTS
from bookings.tests.test_quote import stay  # noqa: F401  (fixture)
from properties.models import DateInventory, RoomBlock, RoomInventory


def _unlimited(stay):
    stay['rate'].max_nights = None
    stay['rate'].save(update_fields=['max_nights'])


def _quote(stay, nights):
    check_in = stay['start']
    return APIClient().get(f"/api/v1/properties/{stay['property'].id}/quote/", {
        'room_type_id': stay['room'].id, 'rate_plan_id': stay['rate'].id,
        'check_in': check_in.isoformat(),
        'check_out': (check_in + timedelta(days=nights)).isoformat(),
    })


@pytest.mark.django_db
def test_max_stay_is_a_year():
    assert MAX_STAY_NIGHTS == 365


@pytest.mark.django_db
def test_quote_longer_than_max_stay_is_rejected_before_touching_inventory(stay):
    _unlimited(stay)

    with CaptureQueriesContext(connection) as queries:
        response = _quote(stay, MAX_STAY_NIGHTS + 1)

    assert response.status_code == 400
    assert 'check_out' in str(response.data)
    assert not any('room_inventory' in q['sql'] for q in queries.captured_queries)


@pytest.mark.django_db
def test_quote_far_future_check_out_is_rejected(stay):
    _unlimited(stay)
    response = APIClient().get(f"/api/v1/properties/{stay['property'].id}/quote/", {
        'room_type_id': stay['room'].id, 'rate_plan_id': stay['rate'].id,
        'check_in': stay['start'].isoformat(), 'check_out': '9999-12-31',
    })

    assert response.status_code == 400
    assert 'check_out' in str(response.data)


@pytest.mark.django_db
def test_booking_longer_than_max_stay_creates_no_inventory_rows(stay):
    _unlimited(stay)
    client = APIClient()
    client.force_authenticate(user=stay['guest'])
    rows_before = RoomInventory.objects.count()

    response = client.post('/api/v1/bookings/', {
        'property_id': stay['property'].id, 'room_type_id': stay['room'].id,
        'rate_plan_id': stay['rate'].id, 'check_in': stay['start'].isoformat(),
        'check_out': (stay['start'] + timedelta(days=MAX_STAY_NIGHTS + 1)).isoformat(),
        'guest_count': 1,
    }, format='json')

    assert response.status_code == 400
    assert 'check_out' in str(response.data)
    assert RoomInventory.objects.count() == rows_before


@pytest.mark.django_db
def test_stay_within_the_limit_still_gets_a_normal_answer(stay):
    _unlimited(stay)
    response = _quote(stay, 3)

    assert response.status_code == 200


# The partner bulk tools write one row per day in the range (owner calendar, bulk
# price, external blocks), so their ranges are capped the same way.
BULK_CALLS = {
    'bulk_set_price': lambda s, d_from, d_to: DateInventory.bulk_set_price(s['rate'], d_from, d_to, 50),
    'bulk_set': lambda s, d_from, d_to: RoomInventory.bulk_set(s['room'], d_from, d_to, available_rooms=2),
    'create_block': lambda s, d_from, d_to: RoomBlock.create_block(
        s['room'], d_from, d_to, 1, 'sold elsewhere', s['property'].owner),
}


def _row_counts():
    return DateInventory.objects.count(), RoomInventory.objects.count(), RoomBlock.objects.count()


@pytest.mark.django_db
@pytest.mark.parametrize('method', sorted(BULK_CALLS))
def test_partner_bulk_range_longer_than_a_year_is_rejected(stay, method):
    counts_before = _row_counts()

    with pytest.raises(ValidationError) as error:
        BULK_CALLS[method](stay, stay['start'], stay['start'] + timedelta(days=MAX_STAY_NIGHTS + 1))

    assert 'date_to' in error.value.message_dict
    assert _row_counts() == counts_before
