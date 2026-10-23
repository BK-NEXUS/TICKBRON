"""Back-to-back stays for tests of the one-account rules (two upcoming bookings, no overlapping dates)."""
from datetime import timedelta
from decimal import Decimal

from common.dates import business_today
from properties.models import DateInventory


def stay(testcase, index, nights=2, first_day=10):
    """
    check_in / check_out of the index-th stay of `nights` nights, each starting the day the previous one ends,
    for the hotel fixture of the booking view tests; the nights are added to the inventory when missing.
    """
    check_in = business_today() + timedelta(days=first_day + index * nights)
    for offset in range(nights):
        DateInventory.objects.get_or_create(
            rate_plan=testcase.rate_plan, date=check_in + timedelta(days=offset),
            defaults={'available_rooms': 5, 'booked_rooms': 0, 'price': Decimal('100.00'), 'currency': 'USD',
                      'is_available': True},
        )
    return {'check_in': check_in.isoformat(), 'check_out': (check_in + timedelta(days=nights)).isoformat()}
