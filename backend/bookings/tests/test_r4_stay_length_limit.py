"""
R4 qáwipsizlik tekseriwi: turıw eń kóbi MAX_STAY_NIGHTS tún.

Rate plan max_nights di bos qaldıra aladı ("shekleusiz"). Sonda quote_stay check_out qa shekem hár túnniń
dizimin qurar edi, sol sebepli 9999 jılǵa check_out menen bir anonim GET /quote/ serverdi ~2.9 million sandı
qurıwǵa hám olardı bir SQL IN dizimine jiberiwge májbúr etti; lock=True menen bron sorawı da
bos orındı tekseriwden aldın hár joq túnge RoomInventory qatarın jaratar edi.
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
        'guest_count': 1, 'expected_arrival_time': '14:00',
    }, format='json')

    assert response.status_code == 400
    assert 'check_out' in str(response.data)
    assert RoomInventory.objects.count() == rows_before


@pytest.mark.django_db
def test_stay_within_the_limit_still_gets_a_normal_answer(stay):
    _unlimited(stay)
    response = _quote(stay, 3)

    assert response.status_code == 200


# Partner kóp ǵana quralları aralıqtaǵı hár kúnge bir qatar jazadı (iye kalendarı, kóp baha,
# sırtqı bloklar), sol sebepli olardıń aralıqları da usınday shekleneni.
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
