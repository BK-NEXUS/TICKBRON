"""
QA finding F7: the owner had to type a "Slug" by hand and a clash showed "The fields property, slug must
make a unique set." Now the slug is made from the name and kept unique inside the hotel / room type.
"""
import pytest

from partner.tests.test_property_create_access import (  # noqa: F401  (fixtures)
    client_for, create_requests, inventory, owner, owner_role,
)

ROOM, RATE = 1, 2


def create(owner, inventory, index, **overrides):
    url, body, _ = create_requests(inventory)[index]
    body = {key: value for key, value in body.items() if key != 'slug'}
    return client_for(owner).post(url, {**body, **overrides}, format='json')


@pytest.mark.django_db
class TestSlugFromName:
    @pytest.mark.parametrize('index, name', [(ROOM, 'Deluxe Suite'), (RATE, 'Deluxe Suite')])
    def test_slug_is_made_from_the_name(self, owner, inventory, index, name):
        response = create(owner, inventory, index, name=name)
        assert response.status_code == 201, response.data
        assert response.data['slug'] == 'deluxe-suite'

    @pytest.mark.parametrize('index', [ROOM, RATE])
    def test_same_name_twice_gets_a_number(self, owner, inventory, index):
        slugs = [create(owner, inventory, index, name='Deluxe Suite').data['slug'] for _ in range(3)]
        assert slugs == ['deluxe-suite', 'deluxe-suite-2', 'deluxe-suite-3']

    @pytest.mark.parametrize('index, fallback', [(ROOM, 'room'), (RATE, 'rate')])
    def test_a_name_without_latin_letters_still_gets_a_slug(self, owner, inventory, index, fallback):
        first = create(owner, inventory, index, name='Люкс').data['slug']
        second = create(owner, inventory, index, name='Стандарт').data['slug']
        assert (first, second) == (fallback, f'{fallback}-2')

    def test_a_slug_that_is_sent_is_kept(self, owner, inventory):
        response = create(owner, inventory, ROOM, name='Deluxe', slug='my-own')
        assert response.data['slug'] == 'my-own'

    def test_a_sent_slug_that_is_taken_is_still_refused(self, owner, inventory):
        create(owner, inventory, ROOM, name='Deluxe', slug='same')
        assert create(owner, inventory, ROOM, name='Other', slug='same').status_code == 400

    def test_numbering_is_per_parent(self, owner, inventory):
        other = type(inventory['room']).objects.create(
            property=inventory['property'], name='Other', slug='other', base_occupancy=1, max_occupancy=2,
            base_price=50, currency='USD', total_rooms=1)
        create(owner, inventory, RATE, name='Flex')
        response = create(owner, inventory, RATE, name='Flex', room_type=other.id)
        assert response.data['slug'] == 'flex'

    def test_editing_the_name_keeps_the_slug(self, owner, inventory):
        room = inventory['room']
        response = client_for(owner).patch(f'/api/v1/partner/rooms/{room.id}/', {'name': 'Renamed'}, format='json')
        assert response.status_code == 200
        assert response.data['slug'] == room.slug
