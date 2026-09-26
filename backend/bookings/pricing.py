"""
The one place a stay is priced.

Booking.create_booking charges what quote_stay returns, and the public quote
endpoint shows the same result before booking, so the total a guest sees is
the amount they pay.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import List

from django.core.exceptions import ValidationError


@dataclass
class StayQuote:
    check_in: date
    check_out: date
    number_of_rooms: int
    currency: str
    # (date, price of one room that night), in date order
    nights: List[tuple] = field(default_factory=list)
    # The locked DateInventory rows (only when quote_stay(..., lock=True))
    inventory: list = field(default_factory=list)

    @property
    def number_of_nights(self):
        return len(self.nights)

    @property
    def nightly_total(self):
        """Price of one room for the whole stay."""
        return sum((price for _, price in self.nights), Decimal('0'))

    @property
    def total_price(self):
        return self.nightly_total * self.number_of_rooms


def _nights(check_in, check_out):
    day = check_in
    while day < check_out:
        yield day
        day += timedelta(days=1)


def quote_stay(rate_plan, check_in, check_out, number_of_rooms=1, lock=False):
    """
    Price a stay: each night costs its own inventory price, or the rate plan's
    base price when the night has none. Every night must be open with enough
    rooms left, and the stay must meet the rate plan's and each night's
    minimum/maximum stay.

    Raises ValidationError naming the field and, for availability, the date.
    With lock=True the inventory rows are locked (call inside transaction.atomic()).
    """
    from properties.models import DateInventory

    if check_out <= check_in:
        raise ValidationError({'check_out': 'Check-out date must be after check-in date'})

    number_of_nights = (check_out - check_in).days
    if rate_plan.min_nights and number_of_nights < rate_plan.min_nights:
        raise ValidationError({
            'check_in': f'Minimum stay is {rate_plan.min_nights} nights for this rate.'
        })
    if rate_plan.max_nights and number_of_nights > rate_plan.max_nights:
        raise ValidationError({
            'check_in': f'Maximum stay is {rate_plan.max_nights} nights for this rate.'
        })

    rows = DateInventory.objects.filter(
        rate_plan=rate_plan, date__gte=check_in, date__lt=check_out, is_deleted=False,
    ).order_by('date')
    if lock:
        rows = rows.select_for_update()
    by_date = {row.date: row for row in rows}

    quote = StayQuote(
        check_in=check_in, check_out=check_out,
        number_of_rooms=number_of_rooms, currency=rate_plan.currency,
    )
    for night in _nights(check_in, check_out):
        row = by_date.get(night)
        if row is None or not row.is_available:
            raise ValidationError({'availability': f'{night.isoformat()} is not available.'})
        if row.remaining_rooms < number_of_rooms:
            raise ValidationError({'availability': f'No rooms left on {night.isoformat()}.'
                                   if row.remaining_rooms == 0 else
                                   f'Only {row.remaining_rooms} rooms left on {night.isoformat()}.'})
        if row.minimum_stay and number_of_nights < row.minimum_stay:
            raise ValidationError({'availability': (
                f'A stay including {night.isoformat()} must be at least {row.minimum_stay} nights.')})
        if row.maximum_stay and number_of_nights > row.maximum_stay:
            raise ValidationError({'availability': (
                f'A stay including {night.isoformat()} can be at most {row.maximum_stay} nights.')})
        price = row.price if row.price is not None else rate_plan.base_price
        quote.nights.append((night, price))
        quote.inventory.append(row)
    return quote
