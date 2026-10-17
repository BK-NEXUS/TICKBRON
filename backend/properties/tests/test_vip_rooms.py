"""
R9 VIP rooms (.ai/PLAN_R9_VIP.md v2): the hotel owner marks a room type as VIP, or not, whenever they want;
no admin approval. Guests see the flag, and VIP room types come first on the property page.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from bookings.tests.test_quote import stay  # noqa: F401  (fixture: property, room, rate plan, guest)
from permissions.models import Role
from properties.models import RoomType
from users.models import User

P = '/api/v1/partner'


def owner_client(user):
    role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
    user.role = role
    user.save()
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def add_room(prop, name, vip=False):
    return RoomType.objects.create(
        property=prop, name=name, slug=name.lower().replace(' ', '-'), base_occupancy=2, max_occupancy=2,
        base_price=60, currency='USD', total_rooms=2, is_vip=vip)


@pytest.mark.django_db
class TestTheFlag:

    def test_a_room_type_is_not_vip_by_default(self, stay):
        assert stay['room'].is_vip is False
        assert RoomType.objects.get(pk=stay['room'].pk).is_vip is False


@pytest.mark.django_db
class TestGuestsSeeIt:

    def rooms(self, stay):
        data = APIClient().get(f"/api/v1/properties/{stay['property'].id}/").data
        return data['room_types']

    def test_every_room_type_on_the_property_page_says_whether_it_is_vip(self, stay):
        add_room(stay['property'], 'Penthouse', vip=True)
        flags = {room['name']: room['is_vip'] for room in self.rooms(stay)}
        assert flags == {'Standard': False, 'Penthouse': True}

    def test_vip_rooms_come_first_the_rest_keep_their_order(self, stay):
        add_room(stay['property'], 'Zeta Suite', vip=True)
        add_room(stay['property'], 'Alpha Suite', vip=True)
        add_room(stay['property'], 'Budget')
        names = [room['name'] for room in self.rooms(stay)]
        assert names == ['Alpha Suite', 'Zeta Suite', 'Budget', 'Standard']

    def test_without_any_vip_room_the_order_is_the_usual_one(self, stay):
        add_room(stay['property'], 'Budget')
        assert [room['name'] for room in self.rooms(stay)] == ['Budget', 'Standard']

    def test_the_availability_list_has_the_flag_and_the_same_order(self, stay):
        add_room(stay['property'], 'Penthouse', vip=True)
        response = APIClient().get(f"/api/v1/properties/{stay['property'].id}/availability/", {
            'check_in': stay['start'].isoformat(), 'check_out': (stay['start'] + timedelta(days=1)).isoformat(),
        })
        assert response.status_code == 200, response.data
        rooms = response.data['room_types']
        assert [room['name'] for room in rooms] == ['Penthouse', 'Standard']
        assert [room['is_vip'] for room in rooms] == [True, False]


@pytest.mark.django_db
class TestOwnerSetsIt:

    def create(self, client, stay, **extra):
        return client.post(f'{P}/rooms/', {
            'property': stay['property'].id, 'name': 'Royal', 'slug': 'royal', 'base_occupancy': 2,
            'max_occupancy': 3, 'base_price': '150.00', 'currency': 'USD', 'total_rooms': 1, **extra,
        }, format='json')

    def test_the_owner_creates_a_vip_room_type(self, stay):
        response = self.create(owner_client(stay['property'].owner), stay, is_vip=True)
        assert response.status_code == 201, response.data
        assert response.data['is_vip'] is True
        assert RoomType.objects.get(slug='royal').is_vip is True

    def test_leaving_it_out_creates_an_ordinary_room_type(self, stay):
        response = self.create(owner_client(stay['property'].owner), stay)
        assert response.status_code == 201
        assert RoomType.objects.get(slug='royal').is_vip is False

    def test_the_owner_turns_it_on_and_off_whenever_they_want(self, stay):
        client = owner_client(stay['property'].owner)
        url = f"{P}/rooms/{stay['room'].id}/"
        assert client.patch(url, {'is_vip': True}, format='json').status_code == 200
        assert RoomType.objects.get(pk=stay['room'].pk).is_vip is True
        assert client.patch(url, {'is_vip': False}, format='json').status_code == 200
        assert RoomType.objects.get(pk=stay['room'].pk).is_vip is False

    def test_the_owners_room_list_shows_it(self, stay):
        add_room(stay['property'], 'Penthouse', vip=True)
        data = owner_client(stay['property'].owner).get(f'{P}/rooms/').data
        results = data.get('results', data)
        assert {row['name']: row['is_vip'] for row in results} == {'Standard': False, 'Penthouse': True}

    def test_editing_other_fields_keeps_it(self, stay):
        room = add_room(stay['property'], 'Penthouse', vip=True)
        response = owner_client(stay['property'].owner).patch(f'{P}/rooms/{room.id}/', {'total_rooms': 5}, format='json')
        assert response.status_code == 200
        assert RoomType.objects.get(pk=room.pk).is_vip is True

    def test_a_value_that_is_not_a_boolean_is_refused(self, stay):
        response = owner_client(stay['property'].owner).patch(
            f"{P}/rooms/{stay['room'].id}/", {'is_vip': 'maybe'}, format='json')
        assert response.status_code == 400
        assert RoomType.objects.get(pk=stay['room'].pk).is_vip is False

    def test_another_owner_cannot_change_it(self, stay):
        other = User.objects.create_user(email='intruder@example.com', password='x')
        response = owner_client(other).patch(f"{P}/rooms/{stay['room'].id}/", {'is_vip': True}, format='json')
        assert response.status_code in (403, 404)
        assert RoomType.objects.get(pk=stay['room'].pk).is_vip is False

    def test_another_owner_cannot_create_a_vip_room_in_someone_elses_hotel(self, stay):
        other = User.objects.create_user(email='intruder2@example.com', password='x')
        response = self.create(owner_client(other), stay, is_vip=True)
        assert response.status_code in (400, 403)
        assert not RoomType.objects.filter(slug='royal').exists()

    def test_a_guest_and_an_anonymous_visitor_cannot_change_it(self, stay):
        url = f"{P}/rooms/{stay['room'].id}/"
        guest = APIClient()
        guest.force_authenticate(user=stay['guest'])
        assert guest.patch(url, {'is_vip': True}, format='json').status_code in (403, 404)
        assert APIClient().patch(url, {'is_vip': True}, format='json').status_code in (401, 403)
        assert RoomType.objects.get(pk=stay['room'].pk).is_vip is False
