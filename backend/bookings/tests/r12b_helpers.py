"""Shared helpers for the R12 phase 3 (no-show reports and the refund) tests."""
from datetime import timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from bookings.models import Booking, BookingItem
from common.dates import business_today
from payments.models import PaymentTransaction
from permissions.models import Role
from properties.models import Property, PropertyType, RatePlan, RoomType
from users.models import User

P = '/api/v1/partner'
A = '/api/v1/admin-panel'
UZS_PRICE = Decimal('1177295')      # per night; 2 nights -> 2 354 590 (the plan's example)


def client_for(user):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def report_url(booking):
    return f'{P}/bookings/{booking.pk}/no-show-report/'


def make_hotel(owner, name='Alpha', currency='UZS', rooms=3):
    hotel_type, _ = PropertyType.objects.get_or_create(name='Hotel', slug='hotel')
    prop = Property.objects.create(
        owner=owner, property_type=hotel_type, status='active', max_guests=2, bedrooms=1, bathrooms=1,
        address_line1=f'1 {name} Street', city='Tashkent', country='Uzbekistan', base_price=500000,
        currency=currency,
    )
    room = RoomType.objects.create(
        property=prop, name='Standard', slug=f'standard-{prop.pk}', base_occupancy=2, max_occupancy=2,
        base_price=500000, currency=currency, total_rooms=rooms,
    )
    rate = RatePlan.objects.create(
        room_type=room, name='Standard Rate', slug=f'standard-rate-{prop.pk}', rate_type='standard',
        base_price=500000, currency=currency,
    )
    return prop, room, rate


def make_stay(prop, guest, check_in, nights=2, status='confirmed', percent=50, price=UZS_PRICE, rooms=1,
              room=None, rate=None, paid=True, currency='UZS'):
    """
    A booking row as the engine leaves it, with the no-show refund snapshot `percent`, its
    booking item (when room and rate are given) and, when `paid`, one completed payment of
    the whole charge.
    """
    booking = Booking.objects.create(
        guest=guest, property=prop, status=status,
        payment_status='paid' if status in ('confirmed', 'completed', 'no_show') else 'pending',
        check_in=check_in, check_out=check_in + timedelta(days=nights), number_of_nights=nights,
        number_of_rooms=rooms, guest_count=1, total_price=price * nights * rooms, currency=currency,
        guest_full_name='Test Guest', guest_email=guest.email, expires_at=None,
        no_show_refund_percent=percent,
    )
    if room is not None and rate is not None:
        BookingItem.objects.create(
            booking=booking, room_type=room, rate_plan=rate, number_of_rooms=rooms,
            price_per_night=price, currency=currency,
        )
    if paid:
        pay(booking)
    return booking


def pay(booking, amount=None, provider='payme', status='completed'):
    """One payment row (written with update(): the model wants one full charge)."""
    n = PaymentTransaction.objects.count()
    tx = PaymentTransaction.objects.create(
        idempotency_key=f'r12b-{booking.pk}-{n}', booking=booking, provider=provider,
        amount=booking.charge_amount, currency=booking.charge_currency, status='completed',
        provider_transaction_id=f'r12b-ptx-{booking.pk}-{n}',
    )
    if amount is not None or status != 'completed':
        PaymentTransaction.objects.filter(pk=tx.pk).update(
            amount=Decimal(amount) if amount is not None else tx.amount, status=status)
        tx.refresh_from_db()
    return tx


@pytest.fixture
def world(db):
    """Two hotel owners with a hotel each, a guest, a staff member and a super-admin."""
    owner_role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
    people = {
        'guest': User.objects.create_user(email='guest@example.com', password='x', full_name='Gita Guest'),
        'owner': User.objects.create_user(email='owner@example.com', password='x', role=owner_role),
        'other_owner': User.objects.create_user(email='owner2@example.com', password='x', role=owner_role),
        'staff': User.objects.create_user(email='staff@example.com', password='x', is_staff=True),
        'super': User.objects.create_user(email='super@example.com', password='x', is_staff=True,
                                          is_superuser=True),
    }
    prop, room, rate = make_hotel(people['owner'], 'Alpha')
    other_prop, other_room, other_rate = make_hotel(people['other_owner'], 'Beta')
    today = business_today()
    return {
        **people, 'prop': prop, 'room': room, 'rate': rate, 'other_prop': other_prop,
        'other_room': other_room, 'other_rate': other_rate, 'today': today,
    }


def past_stay(world, days_ago_check_in=3, nights=2, **kwargs):
    """A confirmed stay of the first hotel that started `days_ago_check_in` days ago."""
    return make_stay(world['prop'], world['guest'], world['today'] - timedelta(days=days_ago_check_in),
                     nights=nights, room=world['room'], rate=world['rate'], **kwargs)


COMMENT = 'The guest never arrived and did not call the reception.'
DECISION = 'Checked with the hotel: the guest did not arrive.'
