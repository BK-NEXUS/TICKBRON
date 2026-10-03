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
from django.db import IntegrityError, transaction

# Longest stay anyone can quote or book, whatever the rate plan allows. Without it a
# far-away check_out made quote_stay build (and lock) one row per night (R4 security review).
MAX_STAY_NIGHTS = 365


@dataclass
class StayQuote:
    check_in: date
    check_out: date
    number_of_rooms: int
    currency: str
    # (date, price of one room that night), in date order
    nights: List[tuple] = field(default_factory=list)
    # The DateInventory rows: price and rate-plan rules (open/closed, min/max stay)
    inventory: list = field(default_factory=list)
    # The RoomInventory rows: physical room count, shared by every rate plan of the
    # room type (locked only when quote_stay(..., lock=True))
    room_inventory: list = field(default_factory=list)

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


def _room_inventory_rows(room_type, nights, lock=False):
    """
    One RoomInventory row per night for this room type. A night with no row
    yet is unmanaged: it is open with the room type's full total_rooms.

    With lock=False the missing rows are not written, only returned as
    in-memory defaults (safe for a read-only quote preview). With lock=True
    they are select_for_update()'d, creating (and locking) any that are
    still missing -- call inside transaction.atomic().
    """
    from properties.models import RoomInventory

    qs = RoomInventory.objects.filter(room_type=room_type, date__in=nights)
    if lock:
        qs = qs.select_for_update()
    rows = {row.date: row for row in qs}

    missing = [night for night in nights if night not in rows]
    if not missing:
        return rows

    if not lock:
        for night in missing:
            rows[night] = RoomInventory(
                room_type=room_type, date=night, available_rooms=room_type.total_rooms,
            )
        return rows

    for night in missing:
        try:
            with transaction.atomic():
                rows[night] = RoomInventory.objects.create(
                    room_type=room_type, date=night, available_rooms=room_type.total_rooms,
                )
        except IntegrityError:
            # Lost the race to create it; the winner's row is now committed and lockable.
            rows[night] = RoomInventory.objects.select_for_update().get(room_type=room_type, date=night)
    return rows


def quote_stay(rate_plan, check_in, check_out, number_of_rooms=1, lock=False):
    """
    Price a stay: each night costs its own inventory price, or the rate plan's
    base price when the night has none. Every night must have its rate plan
    open (DateInventory) with enough physical rooms left (RoomInventory,
    shared by every rate plan of the room type -- audit #31), and the stay
    must meet the rate plan's and each night's minimum/maximum stay.

    Raises ValidationError naming the field and, for availability, the date.
    With lock=True the inventory rows are locked (call inside transaction.atomic()).
    """
    from properties.models import DateInventory

    if check_out <= check_in:
        raise ValidationError({'check_out': 'Check-out date must be after check-in date'})

    number_of_nights = (check_out - check_in).days
    if number_of_nights > MAX_STAY_NIGHTS:
        raise ValidationError({'check_out': f'A stay can be at most {MAX_STAY_NIGHTS} nights.'})
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

    nights = list(_nights(check_in, check_out))
    room_rows = _room_inventory_rows(rate_plan.room_type, nights, lock=lock)

    quote = StayQuote(
        check_in=check_in, check_out=check_out,
        number_of_rooms=number_of_rooms, currency=rate_plan.currency,
    )
    for night in nights:
        row = by_date.get(night)
        if row is None or not row.is_available:
            raise ValidationError({'availability': f'{night.isoformat()} is not available.'})
        if row.minimum_stay and number_of_nights < row.minimum_stay:
            raise ValidationError({'availability': (
                f'A stay including {night.isoformat()} must be at least {row.minimum_stay} nights.')})
        if row.maximum_stay and number_of_nights > row.maximum_stay:
            raise ValidationError({'availability': (
                f'A stay including {night.isoformat()} can be at most {row.maximum_stay} nights.')})

        room_row = room_rows[night]
        if not room_row.is_available:
            raise ValidationError({'availability': f'{night.isoformat()} is not available.'})
        if room_row.remaining_rooms < number_of_rooms:
            raise ValidationError({'availability': f'No rooms left on {night.isoformat()}.'
                                   if room_row.remaining_rooms == 0 else
                                   f'Only {room_row.remaining_rooms} rooms left on {night.isoformat()}.'})

        price = row.price if row.price is not None else rate_plan.base_price
        quote.nights.append((night, price))
        quote.inventory.append(row)
        quote.room_inventory.append(room_row)
    return quote
