"""
R4 security review: a guest cannot read or change another guest's objects by
putting their id in the URL or body (booking, payment, favorite, review,
notification, account history). Hotel-owner to hotel-owner isolation is covered
by partner/tests/test_access_matrix.py and the partner block/inventory tests.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import AccountHistory, Favorite, Notification, Review
from bookings.models import Booking
from payments.models import PaymentTransaction
from properties.models import Property, PropertyType
from users.models import User


@pytest.fixture
def world(db):
    alice = User.objects.create_user(email='alice@example.com', password='x')
    bob = User.objects.create_user(email='bob@example.com', password='x')
    prop = Property.objects.create(
        owner=User.objects.create_user(email='owner@example.com', password='x'),
        property_type=PropertyType.objects.create(name='Hotel', slug='hotel'), status='active',
        max_guests=2, bedrooms=1, bathrooms=1, city='Tashkent', country='Uzbekistan',
        base_price=Decimal('50'), currency='USD',
    )
    check_in = timezone.localdate() - timedelta(days=10)
    booking = Booking.objects.create(
        guest=alice, property=prop, status='completed', payment_status='paid', check_in=check_in,
        check_out=check_in + timedelta(days=2), number_of_nights=2, guest_count=1,
        total_price=Decimal('100'), currency='USD', confirmation_code='ALI001',
    )
    pending = Booking.objects.create(
        guest=alice, property=prop, status='pending', payment_status='pending',
        check_in=timezone.localdate() + timedelta(days=5), check_out=timezone.localdate() + timedelta(days=6),
        number_of_nights=1, guest_count=1, total_price=Decimal('50'), currency='USD',
        confirmation_code='ALI002', expires_at=timezone.now() + timedelta(minutes=15),
    )
    payment = PaymentTransaction.objects.create(
        idempotency_key='alice-key', booking=booking, provider='payme', amount=Decimal('100'),
        currency='USD', status='completed', provider_transaction_id='txn-alice',
    )
    objects = {
        'booking': booking, 'pending': pending, 'payment': payment,
        'favorite': Favorite.objects.create(user=alice, property=prop),
        'review': Review.objects.create(
            user=alice, property=prop, booking=booking, overall_rating=5, title='Nice', comment='Good stay',
        ),
        'notification': Notification.objects.create(
            user=alice, notification_type='booking_confirmed', title='Booked', message='Your booking',
        ),
        'history': AccountHistory.objects.create(user=alice, action='login', description='Logged in'),
        'property': prop, 'alice': alice,
    }
    client = APIClient()
    client.force_authenticate(user=bob)
    return client, objects


READ_URLS = {
    'booking': '/api/v1/bookings/{id}/',
    'payment': '/api/v1/payments/transactions/{id}/',
    'favorite': '/api/v1/me/favorites/{id}/',
    'review': '/api/v1/me/reviews/{id}/',
    'notification': '/api/v1/me/notifications/{id}/',
    'history': '/api/v1/me/history/{id}/',
}


@pytest.mark.django_db
@pytest.mark.parametrize('kind', sorted(READ_URLS))
def test_cannot_read_another_guests_object(world, kind):
    client, objects = world
    response = client.get(READ_URLS[kind].format(id=objects[kind].id))
    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize('kind, method, body', [
    ('favorite', 'patch', {'notes': 'mine now'}),
    ('favorite', 'delete', None),
    ('review', 'patch', {'comment': 'edited by bob'}),
    ('review', 'delete', None),
    ('notification', 'patch', {'is_read': True}),
    ('notification', 'delete', None),
])
def test_cannot_change_another_guests_object(world, kind, method, body):
    client, objects = world
    obj = objects[kind]
    before = type(obj).objects.filter(pk=obj.pk).values().get()

    response = getattr(client, method)(READ_URLS[kind].format(id=obj.id), body or {}, format='json')

    assert response.status_code == 404
    assert type(obj).objects.filter(pk=obj.pk).values().get() == before


@pytest.mark.django_db
def test_lists_show_only_own_objects(world):
    client, _ = world
    for url in ('/api/v1/bookings/', '/api/v1/payments/transactions/', '/api/v1/me/favorites/',
                '/api/v1/me/reviews/', '/api/v1/me/notifications/', '/api/v1/me/history/',
                '/api/v1/payments/audit-logs/'):
        data = client.get(url).data
        rows = data['results'] if isinstance(data, dict) and 'results' in data else data
        assert len(rows) == 0, url


@pytest.mark.django_db
def test_cannot_cancel_another_guests_booking(world):
    client, objects = world
    response = client.post(f"/api/v1/bookings/{objects['pending'].id}/cancel/", {}, format='json')

    assert response.status_code == 404
    objects['pending'].refresh_from_db()
    assert objects['pending'].status == 'pending'


@pytest.mark.django_db
def test_cannot_pay_for_another_guests_booking(world):
    client, objects = world
    response = client.post('/api/v1/payments/transactions/', {
        'idempotency_key': 'bob-key', 'booking': objects['pending'].id, 'provider': 'payme',
        'amount': '50.00', 'currency': 'USD',
    }, format='json')

    assert response.status_code == 400
    assert not PaymentTransaction.objects.filter(idempotency_key='bob-key').exists()


@pytest.mark.django_db
def test_cannot_review_another_guests_stay(world):
    client, objects = world
    Review.objects.all().delete()
    response = client.post('/api/v1/me/reviews/', {
        'property': objects['property'].id, 'booking': objects['booking'].id,
        'overall_rating': 1, 'title': 'Fake', 'comment': 'Never stayed here',
    }, format='json')

    assert response.status_code == 400
    assert not Review.objects.exists()


@pytest.mark.django_db
def test_owner_id_in_body_is_ignored_on_favorite_create(world):
    client, objects = world
    Favorite.objects.all().delete()
    response = client.post('/api/v1/me/favorites/', {
        'property': objects['property'].id, 'user': objects['alice'].id,
    }, format='json')

    assert response.status_code == 201
    assert Favorite.objects.get().user.email == 'bob@example.com'
