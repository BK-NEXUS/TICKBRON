"""
QA finding F5: the owner forms accepted values that make no sense (a rate plan with min 10 and max 2
nights, a room for 2 guests with 4 as the usual number, 0 or 100000 rooms, a free hotel, 999 bathrooms,
nights in the past, more rooms on a night than the room type has). The API answers 400 naming the field.
"""
from datetime import timedelta

import pytest

from common.dates import business_today
from partner.tests.test_property_create_access import (  # noqa: F401  (fixtures)
    client_for, create_requests, inventory, owner, owner_role,
)
from properties.models import DateInventory

P = '/api/v1/partner'
PROPERTY, ROOM, RATE, NIGHT = 0, 1, 2, 3


def payload_of(inventory, index, **overrides):
    url, body, _ = create_requests(inventory)[index]
    return url, {**body, **overrides}


def refused(response):
    """The fields the 400 names."""
    return response.data['error']['details']


REFUSED = [
    (PROPERTY, {'base_price': '0'}, 'base_price'),
    (PROPERTY, {'bathrooms': 999}, 'bathrooms'),
    (PROPERTY, {'bedrooms': 999}, 'bedrooms'),
    (ROOM, {'base_occupancy': 4, 'max_occupancy': 2}, 'max_occupancy'),
    (ROOM, {'max_occupancy': 99}, 'max_occupancy'),
    (ROOM, {'total_rooms': 0}, 'total_rooms'),
    (ROOM, {'total_rooms': 100000}, 'total_rooms'),
    (ROOM, {'base_price': '0'}, 'base_price'),
    (RATE, {'min_nights': 10, 'max_nights': 2}, 'max_nights'),
    (RATE, {'max_nights': 99999}, 'max_nights'),
    (RATE, {'min_nights': 999}, 'min_nights'),
    (NIGHT, {'available_rooms': 9999}, 'available_rooms'),
    (NIGHT, {'minimum_stay': 5, 'maximum_stay': 2}, 'maximum_stay'),
]


@pytest.mark.django_db
class TestCreateRefusesNonsense:
    @pytest.mark.parametrize('index, overrides, field', REFUSED)
    def test_refused_with_the_field_named(self, owner, inventory, index, overrides, field):
        url, body = payload_of(inventory, index, **overrides)
        response = client_for(owner).post(url, body, format='json')
        assert response.status_code == 400, response.data
        assert field in refused(response)

    def test_a_night_in_the_past_is_refused(self, owner, inventory):
        yesterday = (business_today() - timedelta(days=1)).isoformat()
        url, body = payload_of(inventory, NIGHT, date=yesterday)
        response = client_for(owner).post(url, body, format='json')
        assert response.status_code == 400
        assert 'date' in refused(response)

    def test_sensible_values_still_pass(self, owner, inventory):
        client = client_for(owner)
        for index, overrides in [
            (ROOM, {'base_occupancy': 2, 'max_occupancy': 2, 'total_rooms': 1}),
            (RATE, {'min_nights': 2, 'max_nights': 2}),
            (RATE, {'min_nights': 1, 'max_nights': None, 'slug': 'open'}),
            (NIGHT, {'available_rooms': inventory['room'].total_rooms}),
        ]:
            url, body = payload_of(inventory, index, **overrides)
            response = client.post(url, body, format='json')
            assert response.status_code == 201, (index, response.data)


@pytest.mark.django_db
class TestUpdateKeepsTheSameRules:
    def test_rate_plan_max_below_the_saved_min_is_refused(self, owner, inventory):
        inventory['rate'].min_nights = 3
        inventory['rate'].save()
        response = client_for(owner).patch(
            f"{P}/rates/{inventory['rate'].id}/", {'max_nights': 2}, format='json')
        assert response.status_code == 400
        assert 'max_nights' in refused(response)

    def test_room_occupancy_is_checked_against_the_saved_value(self, owner, inventory):
        response = client_for(owner).patch(
            f"{P}/rooms/{inventory['room'].id}/", {'max_occupancy': 1}, format='json')
        assert response.status_code == 400
        assert 'max_occupancy' in refused(response)

    def test_a_night_cannot_be_moved_into_the_past(self, owner, inventory):
        yesterday = (business_today() - timedelta(days=1)).isoformat()
        response = client_for(owner).patch(
            f"{P}/inventory/{inventory['day'].id}/", {'date': yesterday}, format='json')
        assert response.status_code == 400
        assert 'date' in refused(response)

    def test_a_past_night_can_still_be_edited_when_its_date_stays(self, owner, inventory):
        past = DateInventory.objects.create(
            rate_plan=inventory['rate'], date=business_today() - timedelta(days=3), available_rooms=1,
            booked_rooms=0, price=60, currency='USD', is_available=True)
        response = client_for(owner).patch(f'{P}/inventory/{past.id}/', {'notes': 'checked'}, format='json')
        assert response.status_code == 200, response.data
