"""
Reviews reach the public only after the staff approves them, and then show on the hotel page:
a public list of approved reviews (the reviewer as "Aziz K.", never an address) and the staff's moderation list.
"""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from accounts.models import Review
from admin_panel.models import AdminAccessLog
from bookings.models import Booking
from properties.models import Property, PropertyType
from users.models import User

PUBLIC = '/api/v1/me/reviews/public/'
ADMIN = '/api/v1/admin-panel/reviews/'

pytestmark = pytest.mark.django_db


@pytest.fixture
def hotel():
    owner = User.objects.create_user(email='owner@example.com', password='x')
    kind = PropertyType.objects.create(name='Hotel', slug='hotel')
    return Property.objects.create(
        owner=owner, property_type=kind, status='active', max_guests=2, bedrooms=1, bathrooms=1,
        address_line1='1 Main St', city='Tashkent', country='Uzbekistan', base_price=Decimal('60.00'), currency='USD')


def guest(n, full_name='Aziz Karimov'):
    return User.objects.create_user(email=f'guest{n}@example.com', password='x', full_name=full_name)


def review(hotel, user, status='approved', rating=4, comment='Clean and quiet.', **extra):
    return Review.objects.create(user=user, property=hotel, overall_rating=rating, comment=comment, status=status, **extra)


def staff_client(**flags):
    api = APIClient()
    api.force_authenticate(user=User.objects.create_user(email=f'staff{User.objects.count()}@example.com', password='x', **flags))
    return api


class TestPublicList:
    def test_anonymous_sees_only_approved_reviews_newest_first(self, hotel):
        review(hotel, guest(1), comment='first')
        review(hotel, guest(2), comment='second')
        review(hotel, guest(3), status='pending', comment='waiting')
        review(hotel, guest(4), status='rejected', comment='refused')
        gone = review(hotel, guest(5), comment='deleted')
        gone.soft_delete()
        response = APIClient().get(PUBLIC, {'property_id': hotel.id})
        assert response.status_code == 200
        assert [row['comment'] for row in response.data['results']] == ['second', 'first']
        assert response.data['count'] == 2

    def test_the_reviewer_is_a_first_name_and_an_initial_and_nothing_else_personal(self, hotel):
        review(hotel, guest(1, 'Aziz Karimov'))
        row = APIClient().get(PUBLIC, {'property_id': hotel.id}).data['results'][0]
        assert row['reviewer'] == 'Aziz K.'
        assert 'user' not in row and 'user_email' not in row and 'email' not in str(row)

    def test_a_reviewer_with_one_word_or_none_is_still_named_without_leaking(self, hotel):
        review(hotel, guest(1, 'Aziz'))
        review(hotel, User.objects.create_user(email='noname@example.com', password='x'))
        names = {row['reviewer'] for row in APIClient().get(PUBLIC, {'property_id': hotel.id}).data['results']}
        assert names == {'Aziz', ''}

    def test_the_stay_month_comes_from_the_booking(self, hotel):
        user = guest(1)
        booking = Booking.objects.create(
            guest=user, property=hotel, status='completed', check_in=date(2026, 9, 28), check_out=date(2026, 10, 2),
            number_of_nights=4, guest_count=1, total_price=Decimal('240.00'), currency='USD')
        review(hotel, user, booking=booking)
        assert APIClient().get(PUBLIC, {'property_id': hotel.id}).data['results'][0]['stay_month'] == '2026-10'

    def test_ratings_title_and_comment_are_shown(self, hotel):
        review(hotel, guest(1), rating=5, title='Great', cleanliness_rating=5, service_rating=4)
        row = APIClient().get(PUBLIC, {'property_id': hotel.id}).data['results'][0]
        assert (row['overall_rating'], row['title'], row['cleanliness_rating'], row['service_rating']) == (5, 'Great', 5, 4)

    def test_the_property_id_is_needed_and_must_be_a_listed_hotel(self, hotel):
        assert APIClient().get(PUBLIC).status_code == 400
        assert APIClient().get(PUBLIC, {'property_id': 'x'}).status_code == 400
        assert APIClient().get(PUBLIC, {'property_id': 999999}).status_code == 404
        hotel.status = 'suspended'
        hotel.save()
        assert APIClient().get(PUBLIC, {'property_id': hotel.id}).status_code == 404


class TestModerationList:
    def test_staff_sees_waiting_reviews_by_default_with_the_reviewers_address(self, hotel):
        review(hotel, guest(1), status='pending', comment='waiting')
        review(hotel, guest(2), status='approved', comment='shown')
        response = staff_client(is_staff=True).get(ADMIN)
        assert response.status_code == 200
        rows = response.data['results']
        assert [row['comment'] for row in rows] == ['waiting']
        assert rows[0]['reviewer_email'] == 'guest1@example.com'
        assert rows[0]['property_name'] and rows[0]['status'] == 'pending'

    def test_the_status_can_be_chosen(self, hotel):
        review(hotel, guest(1), status='pending')
        review(hotel, guest(2), status='approved')
        review(hotel, guest(3), status='rejected')
        for wanted, count in (('approved', 1), ('rejected', 1), ('pending', 1)):
            rows = staff_client(is_staff=True).get(ADMIN, {'status': wanted}).data['results']
            assert len(rows) == count and rows[0]['status'] == wanted
        assert staff_client(is_staff=True).get(ADMIN, {'status': 'nonsense'}).status_code == 400

    def test_a_guest_and_an_anonymous_visitor_are_refused(self, hotel):
        assert staff_client().get(ADMIN).status_code == 403
        assert APIClient().get(ADMIN).status_code in (401, 403)


class TestDecision:
    def test_approving_shows_the_review_counts_it_and_is_logged(self, hotel):
        row = review(hotel, guest(1), status='pending', rating=2)
        api = staff_client(is_staff=True)
        response = api.post(f'{ADMIN}{row.id}/approve/')
        assert response.status_code == 200 and response.data['status'] == 'approved'
        row.refresh_from_db()
        assert row.status == 'approved' and row.reviewed_at is not None
        assert APIClient().get(PUBLIC, {'property_id': hotel.id}).data['count'] == 1
        scores = APIClient().get('/api/v1/me/reviews/property_scores/', {'property_id': hotel.id}).data
        assert scores['total_reviews'] == 1 and scores['average_rating'] == 2
        assert AdminAccessLog.objects.filter(action='review_approve').count() == 1

    def test_rejecting_hides_the_review_and_is_logged(self, hotel):
        row = review(hotel, guest(1), status='approved')
        response = staff_client(is_staff=True).post(f'{ADMIN}{row.id}/reject/')
        assert response.status_code == 200 and response.data['status'] == 'rejected'
        assert APIClient().get(PUBLIC, {'property_id': hotel.id}).data['count'] == 0
        assert AdminAccessLog.objects.filter(action='review_reject').count() == 1

    def test_only_staff_decide(self, hotel):
        row = review(hotel, guest(1), status='pending')
        assert staff_client().post(f'{ADMIN}{row.id}/approve/').status_code == 403
        assert APIClient().post(f'{ADMIN}{row.id}/approve/').status_code in (401, 403)
        row.refresh_from_db()
        assert row.status == 'pending'

    def test_an_unknown_or_deleted_review_is_a_404(self, hotel):
        gone = review(hotel, guest(1), status='pending')
        gone.soft_delete()
        api = staff_client(is_staff=True)
        assert api.post(f'{ADMIN}{gone.id}/approve/').status_code == 404
        assert api.post(f'{ADMIN}999999/reject/').status_code == 404
