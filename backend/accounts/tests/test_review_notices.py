"""The people of a review are told when staff decide on it: the guest about the decision, the owner about a new review."""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from accounts.models import Notification, Review
from properties.models import Property, PropertyType
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup():
    owner = User.objects.create_user(email='owner@example.com', password='x')
    kind = PropertyType.objects.create(name='Hotel', slug='hotel')
    hotel = Property.objects.create(
        owner=owner, property_type=kind, status='active', max_guests=2, bedrooms=1, bathrooms=1,
        address_line1='1 Main St', city='Tashkent', country='Uzbekistan', base_price=Decimal('60.00'), currency='USD')
    reviewer = User.objects.create_user(email='guest@example.com', password='x', full_name='Aziz Karimov')
    row = Review.objects.create(user=reviewer, property=hotel, overall_rating=5, status='pending')
    staff = APIClient()
    staff.force_authenticate(user=User.objects.create_user(email='staff@example.com', password='x', is_staff=True))
    return owner, reviewer, hotel, row, staff


def notes(user, code):
    return Notification.objects.filter(user=user, code=code)


def test_approving_tells_the_guest_and_the_owner(setup):
    owner, reviewer, hotel, row, staff = setup
    staff.post(f'/api/v1/admin-panel/reviews/{row.id}/approve/')
    params = {'review_id': row.id, 'property_id': hotel.id}
    assert [n.params for n in notes(reviewer, 'review_approved')] == [params]
    assert [n.params for n in notes(owner, 'new_review')] == [params]


def test_rejecting_tells_only_the_guest(setup):
    owner, reviewer, hotel, row, staff = setup
    staff.post(f'/api/v1/admin-panel/reviews/{row.id}/reject/')
    assert notes(reviewer, 'review_rejected').count() == 1
    assert not Notification.objects.filter(user=owner).exists()


def test_the_same_decision_twice_tells_nobody_twice(setup):
    owner, reviewer, hotel, row, staff = setup
    staff.post(f'/api/v1/admin-panel/reviews/{row.id}/approve/')
    staff.post(f'/api/v1/admin-panel/reviews/{row.id}/approve/')
    assert notes(reviewer, 'review_approved').count() == 1
    assert notes(owner, 'new_review').count() == 1


def test_changing_the_decision_tells_the_guest_again(setup):
    owner, reviewer, hotel, row, staff = setup
    staff.post(f'/api/v1/admin-panel/reviews/{row.id}/approve/')
    staff.post(f'/api/v1/admin-panel/reviews/{row.id}/reject/')
    assert notes(reviewer, 'review_rejected').count() == 1


def test_a_failing_notice_does_not_undo_the_decision(setup, monkeypatch):
    owner, reviewer, hotel, row, staff = setup
    monkeypatch.setattr('accounts.review_notices.notify', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('boom')))
    response = staff.post(f'/api/v1/admin-panel/reviews/{row.id}/approve/')
    assert response.status_code == 200
    row.refresh_from_db()
    assert row.status == 'approved'
