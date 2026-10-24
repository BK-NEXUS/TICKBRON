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

from common.money import quantize

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
    # R16: the owner's own price of the rate plan per currency, the main one included
    owner_prices: dict = field(default_factory=dict)

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

    def total_in(self, currency, rate_of=None):
        """
        (amount, source) of the whole stay in `currency`, rounded once to the currency's unit.

        source is 'main' (the plan's own currency), 'owner' (the owner entered a price in that
        currency; a night with its own price keeps the plan's ratio, e.g. +15% in dollars is +15%
        in so'm) or 'converted' (no owner price: the main amount at the CBU rates).
        (None, 'converted') when a rate is missing.
        """
        rate_of = rate_of or current_uzs_rate
        total = Decimal('0')
        source = 'main'
        for _, price in self.nights:
            amount, source = night_price_in(self.currency, self.owner_prices, price, currency, rate_of)
            if amount is None:
                return None, source
            total += amount
        return quantize(total * self.number_of_rooms, currency), source

    def nights_in(self, currency, rate_of=None):
        """[(date, price of one room)] in `currency`, each rounded for display; None when a rate is missing."""
        rate_of = rate_of or current_uzs_rate
        rows = []
        for night, price in self.nights:
            amount, _ = night_price_in(self.currency, self.owner_prices, price, currency, rate_of)
            if amount is None:
                return None
            rows.append((night, quantize(amount, currency)))
        return rows


def current_uzs_rate(currency):
    """so'm per one unit of `currency` from the database, or None without an accepted rate."""
    from currency.rates import current_rate

    info = current_rate(currency)
    return None if info is None else info.rate


def night_price_in(main, owner_prices, price, currency, rate_of):
    """(unrounded price of one room-night in `currency`, source). See StayQuote.total_in."""
    if currency == main:
        return price, 'main'
    if currency in owner_prices:
        base = owner_prices[main]
        owner = owner_prices[currency]
        return (owner * price / base if base else owner), 'owner'
    from_rate, to_rate = rate_of(main), rate_of(currency)
    if from_rate is None or to_rate is None:
        return None, 'converted'
    return price * from_rate / to_rate, 'converted'


def owner_prices_of(rate_plan):
    """{currency: price} the owner entered for a rate plan, the main price included."""
    return {rate_plan.currency: rate_plan.base_price,
            **{row.currency: row.amount for row in rate_plan.prices.all()}}


def rate_lookup(request=None):
    """
    A `rate_of(code)` for the price functions: so'm per one unit, looked up once per currency (and, with a
    request, once per request via currency.rates.rate_for_request); None without an accepted rate.
    """
    from currency.rates import current_rate, rate_for_request

    memo = {}

    def rate_of(code):
        if code not in memo:
            info = rate_for_request(request, code) if request is not None else current_rate(code)
            memo[code] = getattr(info, 'rate', None)
        return memo[code]

    return rate_of


def _listing(prices_by_code):
    from common.money import quantize

    return {code: {'amount': None if amount is None else f'{quantize(amount, code):.2f}', 'source': source}
            for code, (amount, source) in prices_by_code.items()}


def property_price_list(prop, plans, rate_of=None):
    """
    A hotel's "from" price in every supported currency for its cards: the lowest price of its active rate
    plans in that currency (the owner's own, or a conversion), or the hotel's own price converted when it has
    no plan. Same shape as price_list. `plans` are the hotel's active rate plans (prices prefetched).
    """
    from common.money import SUPPORTED_BASE_CURRENCIES

    rate_of = rate_of or current_uzs_rate
    offers = [(plan.currency, owner_prices_of(plan), plan.base_price) for plan in plans] or [
        (prop.currency, {}, prop.base_price)]
    result = {}
    for code in SUPPORTED_BASE_CURRENCIES:
        found = [night_price_in(main, owner, price, code, rate_of) for main, owner, price in offers]
        priced = [item for item in found if item[0] is not None]
        result[code] = min(priced, key=lambda item: item[0]) if priced else (None, found[0][1])
    return _listing(result)


def price_list(rate_plan, rate_of=None):
    """
    The rate plan's price in every supported currency for the API:
    {currency: {'amount': '1250000.00' or None, 'source': 'main' | 'owner' | 'converted'}}.
    """
    from common.money import SUPPORTED_BASE_CURRENCIES

    rate_of = rate_of or current_uzs_rate
    owner = owner_prices_of(rate_plan)
    result = {}
    for code in SUPPORTED_BASE_CURRENCIES:
        amount, source = night_price_in(rate_plan.currency, owner, rate_plan.base_price, code, rate_of)
        result[code] = {'amount': None if amount is None else f'{quantize(amount, code):.2f}', 'source': source}
    return result


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


def _refusal(code, message, night, **params):
    """An availability refusal: the English text stays, and the code with its values lets the site say it in the user's language."""
    return ValidationError({'availability': ValidationError(message, code=code, params={'date': night.isoformat(), **params})})


def availability_reason(error):
    """{'code', 'params'} of an availability refusal, or None for any other kind of refusal."""
    first = (getattr(error, 'error_dict', {}).get('availability') or [None])[0]
    if first is None or not first.code:
        return None
    return {'code': first.code, 'params': first.params}


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
        owner_prices=owner_prices_of(rate_plan),
    )
    for night in nights:
        row = by_date.get(night)
        if row is None or not row.is_available:
            raise _refusal('night_unavailable', f'{night.isoformat()} is not available.', night)
        if row.minimum_stay and number_of_nights < row.minimum_stay:
            raise _refusal(
                'night_min_stay',
                f'A stay including {night.isoformat()} must be at least {row.minimum_stay} nights.',
                night, nights=row.minimum_stay)
        if row.maximum_stay and number_of_nights > row.maximum_stay:
            raise _refusal(
                'night_max_stay',
                f'A stay including {night.isoformat()} can be at most {row.maximum_stay} nights.',
                night, nights=row.maximum_stay)

        room_row = room_rows[night]
        if not room_row.is_available:
            raise _refusal('night_unavailable', f'{night.isoformat()} is not available.', night)
        if room_row.remaining_rooms < number_of_rooms:
            if room_row.remaining_rooms == 0:
                raise _refusal('no_rooms_left', f'No rooms left on {night.isoformat()}.', night)
            raise _refusal(
                'few_rooms_left', f'Only {room_row.remaining_rooms} rooms left on {night.isoformat()}.',
                night, rooms=room_row.remaining_rooms)

        price = row.price if row.price is not None else rate_plan.base_price
        quote.nights.append((night, price))
        quote.inventory.append(row)
        quote.room_inventory.append(room_row)
    return quote
