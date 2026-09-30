"""
Shared data for the Status endpoint tests (admin and partner).

Uzbekistan
  Tashkent   : Alpha Hotel (USD), Beta Hotel (USD)
  (no region): Gamma Hotel (USD)
Kazakhstan
  Almaty     : Delta Hotel (KZT)
"""
from datetime import date
from decimal import Decimal

import pytest

from bookings.models import Booking
from permissions.models import Role
from properties.models import Property, PropertyTranslation, PropertyType
from users.models import User


def make_booking(guest, prop, check_in, price, status='confirmed', currency=None, nights=1):
    return Booking.objects.create(
        guest=guest, property=prop, status=status, payment_status='paid',
        check_in=check_in, check_out=date.fromordinal(check_in.toordinal() + nights),
        number_of_nights=nights, guest_count=1, total_price=Decimal(price),
        currency=currency or prop.currency,
    )


@pytest.fixture
def status_world(db):
    owner_role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
    hotel_type = PropertyType.objects.create(name='Hotel', slug='hotel')
    owner1 = User.objects.create_user(
        email='owner1@example.com', password='OwnerPassword#123', full_name='Olim Owner',
        phone_number='+998901111111', role=owner_role)
    owner2 = User.objects.create_user(
        email='owner2@example.com', password='OwnerPassword#123', full_name='Oydin Owner',
        phone_number='+998902222222', role=owner_role)

    def hotel(owner, name, country, state, city, currency='USD'):
        prop = Property.objects.create(
            owner=owner, property_type=hotel_type, status='active', max_guests=2,
            address_line1=f'1 {name} Street', city=city, state=state, country=country,
            base_price=Decimal('50.00'), currency=currency,
        )
        PropertyTranslation.objects.create(property=prop, language='en', name=name)
        return prop

    alpha = hotel(owner1, 'Alpha Hotel', 'Uzbekistan', 'Tashkent', 'Tashkent')
    beta = hotel(owner1, 'Beta Hotel', 'Uzbekistan', 'Tashkent', 'Tashkent')
    gamma = hotel(owner2, 'Gamma Hotel', 'Uzbekistan', None, 'Chirchiq')
    delta = hotel(owner2, 'Delta Hotel', 'Kazakhstan', 'Almaty', 'Almaty', currency='KZT')

    def guest(n, first, last):
        return User.objects.create_user(
            email=f'guest{n}@example.com', password='GuestPassword#123', first_name=first,
            last_name=last, full_name=f'{first} {last}', phone_number=f'+99890333000{n}')

    g1, g2, g3 = guest(1, 'Aziz', 'Karimov'), guest(2, 'Madina', 'Nazarova'), guest(3, 'Timur', 'Bekov')

    # Counted (confirmed or completed)
    make_booking(g1, alpha, date(2026, 3, 5), '100.00')
    make_booking(g1, alpha, date(2026, 4, 10), '150.00', status='completed')
    make_booking(g2, alpha, date(2026, 4, 12), '200.00')
    make_booking(g2, beta, date(2025, 11, 20), '80.00', status='completed')
    make_booking(g3, beta, date(2026, 4, 1), '60.00', currency='EUR')
    make_booking(g3, delta, date(2026, 4, 2), '50000.00')
    # Not counted
    make_booking(g3, alpha, date(2026, 4, 3), '999.00', status='pending')
    make_booking(g3, alpha, date(2026, 4, 4), '999.00', status='cancelled')
    make_booking(g3, gamma, date(2026, 4, 5), '999.00', status='no_show')
    deleted = make_booking(g1, gamma, date(2026, 4, 6), '999.00')
    deleted.is_deleted = True
    deleted.save()

    return {
        'owners': (owner1, owner2), 'hotels': {'alpha': alpha, 'beta': beta, 'gamma': gamma, 'delta': delta},
        'guests': (g1, g2, g3),
    }
