"""seed_demo_bulk (R14): demo data at volume for performance measurements, local development only."""
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from bookings.models import Booking
from properties.models import DateInventory, Property, RoomInventory
from users.models import User

SMALL = {'hotels': 10, 'guests': 3, 'bookings': 20, 'days': 5}


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_creates_the_requested_volume():
    call_command('seed_demo_bulk', **SMALL)

    assert Property.objects.filter(translations__description__startswith='[BULK]').distinct().count() == 10
    assert User.objects.filter(email__startswith='bulk-guest-').count() == 3
    assert Booking.objects.filter(special_requests__startswith='[BULK]').count() == 20
    # 10 hotels x 2 room types x 5 days, and 2 rate plans per room type
    assert RoomInventory.objects.count() == 100
    assert DateInventory.objects.count() == 200


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_refuses_to_run_twice():
    call_command('seed_demo_bulk', **SMALL)

    with pytest.raises(CommandError, match='already exists'):
        call_command('seed_demo_bulk', **SMALL)


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_refuses_to_run_outside_debug():
    with pytest.raises(CommandError, match='DEBUG'):
        call_command('seed_demo_bulk', **SMALL)
