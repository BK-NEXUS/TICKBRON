"""
Django 6.1 passes `fetch_mode` to Model.from_db() and deprecates (RemovedInDjango2028Warning) a from_db()
that does not accept it. Booking.from_db records the price snapshot, so it must take the keyword and
pass it on, and keep working on the Django version pinned in requirements.txt (which has no such keyword).
"""
import inspect
from datetime import timedelta
from decimal import Decimal

import pytest

from bookings.models import Booking
from bookings.tests.r12_helpers import make_booking
from common.dates import business_today
from properties.models import Property, PropertyType
from users.models import User

pytestmark = pytest.mark.django_db


def test_from_db_accepts_the_fetch_mode_keyword():
    parameters = inspect.signature(Booking.from_db).parameters.values()
    assert any(p.name == 'fetch_mode' or p.kind is inspect.Parameter.VAR_KEYWORD for p in parameters)


def test_a_loaded_booking_still_remembers_its_price_snapshot():
    owner = User.objects.create_user(email='owner-fd@example.com', password='OwnerPassword#123')
    guest = User.objects.create_user(email='guest-fd@example.com', password='GuestPassword#123')
    prop = Property.objects.create(
        owner=owner, property_type=PropertyType.objects.create(name='Hotel', slug='hotel'), status='active',
        max_guests=2, address_line1='1 Main', city='Tashkent', country='Uzbekistan', base_price=60, currency='USD',
    )
    booking = make_booking(prop, guest, business_today() + timedelta(days=10))

    loaded = Booking.objects.get(pk=booking.pk)

    assert loaded._loaded_snapshot['total_price'] == booking.total_price
    assert isinstance(loaded._loaded_snapshot['total_price'], Decimal)
    loaded.total_price += 1
    with pytest.raises(PermissionError):
        loaded.save()
