"""The owner's Status shows how guests rate each hotel: the average, how many reviews, the 1-5 split and the categories."""
import pytest
from rest_framework.test import APIClient

from accounts.models import Review
from promotions.tests.helpers import make_guest, make_hotel, make_owner, make_staff
from users.models import User

pytestmark = pytest.mark.django_db

STATUS = '/api/v1/partner/status/'


def client_of(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.fixture
def owner():
    return make_owner('mine@example.com')


@pytest.fixture
def hotel(owner):
    return make_hotel(owner, name='My Hotel')


def review(hotel, rating, status='approved', **extra):
    guest = User.objects.create_user(email=f'g{User.objects.count()}@example.com', password='x')
    return Review.objects.create(user=guest, property=hotel, overall_rating=rating, status=status, **extra)


def row_of(response, hotel):
    return next(row for row in response.data['properties'] if row['id'] == hotel.id)


class TestTheRowInTheHotelTable:
    def test_the_average_and_the_count_of_the_approved_reviews(self, owner, hotel):
        for rating in (5, 4, 4, 4):
            review(hotel, rating)
        assert row_of(client_of(owner).get(STATUS), hotel)['rating'] == {'count': 4, 'average': '4.3'}

    def test_a_hotel_without_reviews_has_no_average(self, owner, hotel):
        assert row_of(client_of(owner).get(STATUS), hotel)['rating'] == {'count': 0, 'average': None}

    def test_only_approved_reviews_count(self, owner, hotel):
        review(hotel, 5)
        review(hotel, 1, status='pending')
        review(hotel, 1, status='rejected')
        review(hotel, 1).soft_delete()
        assert row_of(client_of(owner).get(STATUS), hotel)['rating'] == {'count': 1, 'average': '5.0'}

    def test_each_hotel_has_its_own_numbers_and_strangers_reviews_stay_out(self, owner, hotel):
        second = make_hotel(owner, name='Second')
        stranger = make_hotel(make_owner('other@example.com'), name='Other')
        review(hotel, 5)
        review(second, 2)
        review(second, 3)
        review(stranger, 1)
        response = client_of(owner).get(STATUS)
        assert row_of(response, hotel)['rating'] == {'count': 1, 'average': '5.0'}
        assert row_of(response, second)['rating'] == {'count': 2, 'average': '2.5'}
        assert len(response.data['properties']) == 2

    def test_the_period_does_not_change_the_rating(self, owner, hotel):
        review(hotel, 4)
        response = client_of(owner).get(STATUS, {'period': 'today'})
        assert row_of(response, hotel)['rating'] == {'count': 1, 'average': '4.0'}


class TestTheHotelDetail:
    def url(self, hotel):
        return f'/api/v1/partner/status/hotels/{hotel.id}/'

    def test_the_split_by_stars_and_the_categories(self, owner, hotel):
        review(hotel, 5, cleanliness_rating=5, location_rating=4, value_rating=3)
        review(hotel, 4, cleanliness_rating=4, location_rating=4)
        review(hotel, 4)
        reviews = client_of(owner).get(self.url(hotel)).data['reviews']
        assert reviews == {
            'count': 3, 'average': '4.3', 'distribution': [0, 0, 0, 2, 1],
            'categories': {'cleanliness': '4.5', 'location': '4.0', 'value': '3.0', 'amenities': None, 'service': None},
        }

    def test_a_hotel_without_reviews(self, owner, hotel):
        reviews = client_of(owner).get(self.url(hotel)).data['reviews']
        assert reviews == {
            'count': 0, 'average': None, 'distribution': [0, 0, 0, 0, 0],
            'categories': {'cleanliness': None, 'location': None, 'value': None, 'amenities': None, 'service': None},
        }

    def test_pending_and_rejected_reviews_are_not_counted(self, owner, hotel):
        review(hotel, 5)
        review(hotel, 1, status='pending')
        assert client_of(owner).get(self.url(hotel)).data['reviews']['distribution'] == [0, 0, 0, 0, 1]

    def test_another_owners_hotel_is_still_a_404(self, owner):
        stranger = make_hotel(make_owner('other@example.com'), name='Other')
        assert client_of(owner).get(self.url(stranger)).status_code == 404


class TestAccessIsUnchanged:
    def test_a_guest_and_a_visitor_are_refused(self):
        assert client_of(make_guest()).get(STATUS).status_code == 403
        assert APIClient().get(STATUS).status_code in (401, 403)

    def test_staff_see_only_their_own_hotels(self, hotel):
        review(hotel, 5)
        assert client_of(make_staff()).get(STATUS).data['properties'] == []
