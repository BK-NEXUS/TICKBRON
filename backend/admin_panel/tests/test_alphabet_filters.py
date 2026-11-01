"""?letter= on the lists of people and hotels: users, customers, hotels, the status lists, the commission list."""
from datetime import date

import pytest
from rest_framework.test import APIClient

from admin_panel.tests.status_fixtures import make_booking
from partner.models import CommissionRate
from promotions.tests.helpers import make_guest, make_hotel, make_owner, make_staff, make_superadmin
from properties.models import PropertyTranslation
from users.models import User

pytestmark = pytest.mark.django_db

A = '/api/v1/admin-panel'


def client_of(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


def person(email, **fields):
    return User.objects.create_user(email=email, password='Kitob7$yy', **fields)


def emails(response):
    return [row['email'] for row in response.data['results']]


@pytest.fixture
def staff():
    return make_staff('staff@example.com')


class TestUsersList:
    @pytest.fixture
    def people(self):
        return {
            'aziz': person('aziz@example.com', full_name='Aziz Karimov'),
            'anvar': person('anvar@example.com', first_name='Anvar', last_name='Tosh'),
            'bobur': person('bobur@example.com', full_name='Bobur Aliev'),
            'cyr': person('cyr@example.com', full_name='Азиз Каримов'),
        }

    def test_the_list_is_paged_not_everything_at_once(self, staff, people):
        for number in range(60):
            person(f'extra{number}@example.com', full_name=f'Extra {number:02d}')

        response = client_of(staff).get(f'{A}/users/')

        assert response.status_code == 200
        assert response.data['count'] == 60 + len(people) + 1  # + the staff account itself
        assert len(response.data['results']) == 50
        assert response.data['next']

    def test_a_page_size_can_be_asked_for_but_has_a_ceiling(self, staff, people):
        assert len(client_of(staff).get(f'{A}/users/', {'page_size': 2}).data['results']) == 2
        for number in range(130):
            person(f'x{number}@example.com')
        assert len(client_of(staff).get(f'{A}/users/', {'page_size': 100000}).data['results']) <= 100

    def test_the_list_is_in_alphabetical_order_of_the_shown_name(self, staff, people):
        names = [row['full_name'] or row['email'] for row in client_of(staff).get(f'{A}/users/').data['results']]

        assert names == sorted(names, key=str.casefold)

    def test_a_letter_keeps_only_the_names_that_start_with_it(self, staff, people):
        response = client_of(staff).get(f'{A}/users/', {'letter': 'a'})

        assert sorted(emails(response)) == ['anvar@example.com', 'aziz@example.com']
        assert response.data['count'] == 2

    def test_cyrillic_and_hash_buckets(self, staff, people):
        assert emails(client_of(staff).get(f'{A}/users/', {'letter': 'А'})) == ['cyr@example.com']
        person('digit@example.com', full_name='7 Seven')
        assert emails(client_of(staff).get(f'{A}/users/', {'letter': '#'})) == ['digit@example.com']

    def test_search_finds_a_name_an_address_or_a_phone(self, staff, people):
        person('phone@example.com', full_name='Zafar', phone_number='+998905554433')
        api = client_of(staff)

        assert emails(api.get(f'{A}/users/', {'search': 'karimov'})) == ['aziz@example.com', 'cyr@example.com'][:1]
        assert emails(api.get(f'{A}/users/', {'search': 'bobur@'})) == ['bobur@example.com']
        assert emails(api.get(f'{A}/users/', {'search': '5554433'})) == ['phone@example.com']

    def test_the_letter_and_the_search_work_together(self, staff, people):
        assert emails(client_of(staff).get(f'{A}/users/', {'letter': 'A', 'search': 'tosh'})) == ['anvar@example.com']

    @pytest.mark.parametrize('role, expected', [
        ('guest', {'aziz@example.com'}), ('owner', {'owner@example.com'}), ('staff', {'staff@example.com'}),
        ('super_admin', {'boss@example.com'}),
    ])
    def test_a_role_can_be_chosen(self, staff, role, expected):
        person('aziz@example.com', full_name='Aziz')
        make_owner('owner@example.com')
        make_superadmin('boss@example.com')

        response = client_of(staff).get(f'{A}/users/', {'role': role})

        assert set(emails(response)) == expected

    @pytest.mark.parametrize('params', [{'letter': 'ab'}, {'letter': '%'}, {'role': 'wizard'}, {'page': 'x'}])
    def test_a_bad_parameter_is_a_clean_4xx(self, staff, people, params):
        assert 400 <= client_of(staff).get(f'{A}/users/', params).status_code < 500

    def test_a_page_size_that_is_not_a_number_means_the_normal_page(self, staff, people):
        assert len(client_of(staff).get(f'{A}/users/', {'page_size': 'x'}).data['results']) <= 50

    @pytest.mark.parametrize('term', ['%', '_', "' OR 1=1 --", 'x' * 500, '\x00'])
    def test_a_hostile_search_is_a_clean_answer(self, staff, people, term):
        assert client_of(staff).get(f'{A}/users/', {'search': term}).status_code in (200, 400)

    def test_guests_and_owners_cannot_use_it_and_the_listing_is_still_logged(self, staff, people):
        from admin_panel.models import AdminAccessLog
        assert client_of(people['aziz']).get(f'{A}/users/', {'letter': 'A'}).status_code == 403
        client_of(staff).get(f'{A}/users/', {'letter': 'A'})
        assert AdminAccessLog.objects.filter(action='user_list', actor_id=staff.id).exists()

    def test_deleted_accounts_are_not_listed(self, staff, people):
        User.objects.filter(pk=people['aziz'].pk).update(is_deleted=True)

        assert 'aziz@example.com' not in emails(client_of(staff).get(f'{A}/users/', {'letter': 'A'}))


class TestCustomersAndStatusUsers:
    @pytest.fixture
    def guests(self):
        return {name: person(f'{name}@example.com', full_name=name.title()) for name in ('aziz', 'bobur', 'anvar')}

    def test_the_customer_directory_takes_a_letter(self, staff, guests):
        response = client_of(staff).get(f'{A}/customers/', {'letter': 'B'})

        assert response.status_code == 200
        assert [row['email'] for row in response.data['results']] == ['bobur@example.com']

    def test_the_customer_directory_refuses_a_bad_letter(self, staff, guests):
        assert client_of(staff).get(f'{A}/customers/', {'letter': 'xy'}).status_code == 400

    def test_the_status_users_list_takes_a_letter(self, staff, guests):
        owner = make_owner('hotelier@example.com')
        hotel = make_hotel(owner, name='Stay Inn')
        for guest in guests.values():
            make_booking(guest, hotel, date(2026, 3, 5), '100.00')

        response = client_of(staff).get(f'{A}/status/users/', {'letter': 'A', 'period': 'all'})

        assert response.status_code == 200
        assert sorted(row['email'] for row in response.data['results']) == ['anvar@example.com', 'aziz@example.com']


class TestHotelLists:
    @pytest.fixture
    def hotels(self):
        owner = make_owner('hotelier@example.com')
        return {
            'grand': make_hotel(owner, name='Grand Hotel'),
            'alpha': make_hotel(owner, name='Alpha Inn'),
            'beta': make_hotel(owner, name='Beta House'),
        }

    def ids(self, response):
        return {row['id'] for row in response.data['results']}

    def test_the_admin_hotel_list_takes_a_letter_and_a_name_in_another_language(self, staff, hotels):
        PropertyTranslation.objects.create(property=hotels['beta'], language='ru', name='Гамма')
        api = client_of(staff)

        assert self.ids(api.get(f'{A}/properties/', {'letter': 'g'})) == {hotels['grand'].id}
        assert self.ids(api.get(f'{A}/properties/', {'letter': 'Г'})) == {hotels['beta'].id}
        assert self.ids(api.get(f'{A}/properties/', {'letter': 'B'})) == {hotels['beta'].id}

    def test_the_admin_hotel_list_can_be_narrowed_by_status_and_search(self, staff, hotels):
        type(hotels['alpha']).objects.filter(pk=hotels['alpha'].pk).update(status='pending')
        api = client_of(staff)

        assert self.ids(api.get(f'{A}/properties/', {'status': 'pending'})) == {hotels['alpha'].id}
        assert self.ids(api.get(f'{A}/properties/', {'search': 'house'})) == {hotels['beta'].id}

    def test_a_bad_letter_on_the_hotel_list_is_a_400(self, staff, hotels):
        assert client_of(staff).get(f'{A}/properties/', {'letter': '%'}).status_code == 400

    def test_the_status_hotel_list_takes_a_letter(self, staff, hotels):
        response = client_of(staff).get(f'{A}/status/hotels/', {'letter': 'A', 'period': 'all'})

        assert response.status_code == 200
        assert [row['name'] for row in response.data['results']] == ['Alpha Inn']

    def test_an_owner_sees_only_their_own_hotels_under_a_letter(self, hotels):
        other = make_owner('other.owner@example.com')
        make_hotel(other, name='Apex Lodge')
        owner = hotels['grand'].owner

        response = client_of(owner).get('/api/v1/partner/properties/', {'letter': 'A'})

        names = [row['name'] for row in response.data['results']]
        assert names == ['Alpha Inn']


class TestCommissionList:
    def test_the_commission_list_takes_a_letter_by_the_owner_name(self, staff):
        aziz = make_owner('aziz.owner@example.com')
        User.objects.filter(pk=aziz.pk).update(full_name='Aziz Egasi')
        bobur = make_owner('bobur.owner@example.com')
        User.objects.filter(pk=bobur.pk).update(full_name='Bobur Egasi')

        response = client_of(staff).get(f'{A}/commission/', {'letter': 'b'})

        assert [row['email'] for row in response.data['results']] == ['bobur.owner@example.com']

    def test_a_bad_letter_is_a_400(self, staff):
        assert client_of(staff).get(f'{A}/commission/', {'letter': '12'}).status_code == 400
