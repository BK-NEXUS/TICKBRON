"""A hotel owner reads the approved reviews of their own hotels and answers them in public."""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from accounts.models import Notification, Review
from permissions.models import Role
from properties.models import Property, PropertyType
from users.models import User

LIST = '/api/v1/partner/reviews/'
PUBLIC = '/api/v1/me/reviews/public/'

pytestmark = pytest.mark.django_db


@pytest.fixture
def role():
    return Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})[0]


@pytest.fixture
def kind():
    return PropertyType.objects.create(name='Hotel', slug='hotel')


def make_hotel(owner, kind, city='Tashkent'):
    return Property.objects.create(
        owner=owner, property_type=kind, status='active', max_guests=2, bedrooms=1, bathrooms=1,
        address_line1='1 Main St', city=city, country='Uzbekistan', base_price=Decimal('60.00'), currency='USD')


@pytest.fixture
def owner(role):
    return User.objects.create_user(email='owner@example.com', password='x', role=role)


@pytest.fixture
def hotel(owner, kind):
    return make_hotel(owner, kind)


def owner_client(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


def guest(n=1):
    return User.objects.create_user(email=f'guest{n}@example.com', password='x', full_name='Aziz Karimov')


def review(hotel, user=None, status='approved', **extra):
    extra.setdefault('comment', 'Clean')
    return Review.objects.create(user=user or guest(), property=hotel, overall_rating=4, status=status, **extra)


class TestList:
    def test_the_owner_sees_the_approved_reviews_of_their_own_hotels_only(self, owner, hotel, kind, role):
        mine = review(hotel, guest(1), comment='mine')
        review(hotel, guest(2), status='pending', comment='waiting')
        review(hotel, guest(3), status='rejected', comment='refused')
        stranger = User.objects.create_user(email='other@example.com', password='x', role=role)
        review(make_hotel(stranger, kind), guest(4), comment='not mine')
        rows = owner_client(owner).get(LIST).data['results']
        assert [row['id'] for row in rows] == [mine.id]
        assert rows[0]['reviewer'] == 'Aziz K.'
        assert rows[0]['property_name'] and rows[0]['owner_reply'] == '' and rows[0]['replied_at'] is None
        assert 'email' not in str(rows[0])

    def test_a_hotel_can_be_picked(self, owner, hotel, kind):
        other = make_hotel(owner, kind, city='Samarkand')
        a, b = review(hotel, guest(1)), review(other, guest(2))
        assert [row['id'] for row in owner_client(owner).get(LIST, {'property': other.id}).data['results']] == [b.id]
        assert len(owner_client(owner).get(LIST).data['results']) == 2

    def test_a_guest_and_an_anonymous_visitor_are_refused(self, hotel):
        assert owner_client(guest()).get(LIST).status_code == 403
        assert APIClient().get(LIST).status_code in (401, 403)


class TestReply:
    def url(self, row):
        return f'{LIST}{row.id}/reply/'

    def test_the_owner_answers_and_the_answer_is_public(self, owner, hotel):
        row = review(hotel)
        response = owner_client(owner).post(self.url(row), {'text': ' Thank you for staying with us! '}, format='json')
        assert response.status_code == 200
        assert response.data['owner_reply'] == 'Thank you for staying with us!' and response.data['replied_at']
        public = APIClient().get(PUBLIC, {'property_id': hotel.id}).data['results'][0]
        assert public['owner_reply'] == 'Thank you for staying with us!' and public['replied_at']

    def test_a_second_answer_replaces_the_first(self, owner, hotel):
        row = review(hotel)
        api = owner_client(owner)
        api.post(self.url(row), {'text': 'first'}, format='json')
        api.post(self.url(row), {'text': 'second'}, format='json')
        row.refresh_from_db()
        assert row.owner_reply == 'second'

    def test_the_answer_can_be_taken_back(self, owner, hotel):
        row = review(hotel)
        api = owner_client(owner)
        api.post(self.url(row), {'text': 'first'}, format='json')
        assert api.delete(self.url(row)).status_code == 204
        row.refresh_from_db()
        assert row.owner_reply == '' and row.replied_at is None

    @pytest.mark.parametrize('text', ['', '   ', 'x' * 1001, '<script>alert(1)</script>'])
    def test_a_bad_answer_is_refused_with_the_field_named(self, owner, hotel, text):
        row = review(hotel)
        response = owner_client(owner).post(self.url(row), {'text': text}, format='json')
        assert response.status_code == 400 and 'text' in str(response.data)
        row.refresh_from_db()
        assert row.owner_reply == ''

    def test_only_the_owner_of_that_hotel_can_answer(self, owner, hotel, kind, role):
        row = review(hotel)
        stranger = User.objects.create_user(email='other@example.com', password='x', role=role)
        assert owner_client(stranger).post(self.url(row), {'text': 'hi'}, format='json').status_code == 404
        assert owner_client(guest(9)).post(self.url(row), {'text': 'hi'}, format='json').status_code == 403
        assert APIClient().post(self.url(row), {'text': 'hi'}, format='json').status_code in (401, 403)

    def test_a_review_that_is_not_public_cannot_be_answered(self, owner, hotel):
        waiting = review(hotel, guest(1), status='pending')
        gone = review(hotel, guest(2))
        gone.soft_delete()
        api = owner_client(owner)
        assert api.post(self.url(waiting), {'text': 'hi'}, format='json').status_code == 404
        assert api.post(self.url(gone), {'text': 'hi'}, format='json').status_code == 404

    def test_the_guest_is_told_about_the_first_answer_only(self, owner, hotel):
        row = review(hotel)
        api = owner_client(owner)
        api.post(self.url(row), {'text': 'first'}, format='json')
        api.post(self.url(row), {'text': 'edited'}, format='json')
        told = Notification.objects.filter(user=row.user, code='review_reply')
        assert told.count() == 1 and told[0].params == {'review_id': row.id, 'property_id': hotel.id}
