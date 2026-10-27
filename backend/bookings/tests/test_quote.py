"""
GET /api/v1/properties/{id}/quote/ prices a stay with the same code that
charges for it, so the total shown before booking is the amount charged.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking
from properties.models import DateInventory, Property, PropertyType, RatePlan, RoomInventory, RoomType
from users.models import User
from currency.testing import make_usd_rate


@pytest.fixture
def stay(db):
    owner = User.objects.create_user(email='owner@example.com', password='OwnerPassword#123')
    prop = Property.objects.create(
        owner=owner, property_type=PropertyType.objects.create(name='Hotel', slug='hotel'),
        status='active', max_guests=2, bedrooms=1, bathrooms=1, address_line1='1 Main',
        city='Tashkent', country='Uzbekistan', base_price=60, currency='USD',
    )
    room = RoomType.objects.create(
        property=prop, name='Standard', slug='standard', base_occupancy=2, max_occupancy=2,
        base_price=60, currency='USD', total_rooms=3,
    )
    rate = RatePlan.objects.create(
        room_type=room, name='Standard Rate', slug='standard-rate', rate_type='standard',
        base_price=Decimal('60.00'), currency='USD', min_nights=1, max_nights=7, is_active=True,
    )
    start = timezone.localdate() + timedelta(days=7)
    days = {}
    for offset in range(10):
        day = start + timedelta(days=offset)
        # Night 2 is a "weekend" night with its own price; night 3 uses the base price
        price = {2: Decimal('69.00'), 3: None}.get(offset, Decimal('60.00'))
        days[offset] = DateInventory.objects.create(
            rate_plan=rate, date=day, available_rooms=3, booked_rooms=0,
            price=price, currency='USD', is_available=True,
        )
    guest = User.objects.create_user(email='guest@example.com', password='GuestPassword#123', phone_number='+998901112233')
    return {'property': prop, 'room': room, 'rate': rate, 'start': start, 'days': days, 'guest': guest}


def quote(stay, first, last, rooms=None):
    params = {
        'room_type_id': stay['room'].id, 'rate_plan_id': stay['rate'].id,
        'check_in': (stay['start'] + timedelta(days=first)).isoformat(),
        'check_out': (stay['start'] + timedelta(days=last)).isoformat(),
    }
    if rooms:
        params['rooms'] = rooms
    return APIClient().get(f"/api/v1/properties/{stay['property'].id}/quote/", params)


@pytest.mark.django_db
class TestQuote:

    def test_one_night_is_priced_with_that_nights_price(self, stay):
        response = quote(stay, 2, 3)  # the 69.00 night alone
        assert response.status_code == 200, response.data
        assert response.data['number_of_nights'] == 1
        assert response.data['total_price'] == '69.00'
        assert response.data['currency'] == 'USD'

    def test_total_is_the_sum_of_each_nights_own_price(self, stay):
        response = quote(stay, 1, 4)  # 60 + 69 + base 60
        assert response.status_code == 200
        assert response.data['number_of_nights'] == 3
        assert [n['price'] for n in response.data['nights']] == ['60.00', '69.00', '60.00']
        assert response.data['total_price'] == '189.00'

    def test_rooms_multiply_the_total(self, stay):
        response = quote(stay, 1, 4, rooms=2)
        assert response.data['total_price'] == '378.00'

    def test_quote_equals_the_amount_charged(self, stay):
        make_usd_rate()  # R6: a USD hotel is bookable only once a rate exists
        shown = quote(stay, 1, 4).data['total_price']
        booking = Booking.create_booking(
            guest=stay['guest'], property_obj=stay['property'], room_type=stay['room'],
            rate_plan=stay['rate'], check_in=stay['start'] + timedelta(days=1),
            check_out=stay['start'] + timedelta(days=4), guest_count=1,
        )
        assert str(booking.total_price) == shown

    def test_closed_night_is_named(self, stay):
        stay['days'][3].is_available = False
        stay['days'][3].save()
        response = quote(stay, 1, 5)
        closed = (stay['start'] + timedelta(days=3)).isoformat()
        assert response.status_code == 400
        assert f'{closed} is not available' in str(response.data['details']['availability'])

    def test_sold_out_night_is_named(self, stay):
        # RoomInventory is what the engine gates room count on (audit #31);
        # DateInventory keeps price and rate rules.
        RoomInventory.objects.create(
            room_type=stay['room'], date=stay['start'] + timedelta(days=2),
            available_rooms=3, booked_rooms=3,
        )
        response = quote(stay, 1, 4)
        sold_out = (stay['start'] + timedelta(days=2)).isoformat()
        assert response.status_code == 400
        assert f'No rooms left on {sold_out}' in str(response.data['details']['availability'])

    def test_missing_inventory_night_is_named(self, stay):
        response = quote(stay, 8, 12)
        missing = (stay['start'] + timedelta(days=10)).isoformat()
        assert response.status_code == 400
        assert f'{missing} is not available' in str(response.data['details']['availability'])

    def test_rate_plan_min_and_max_stay(self, stay):
        stay['rate'].min_nights = 2
        stay['rate'].save()
        too_short = quote(stay, 1, 2)
        too_long = quote(stay, 0, 9)
        assert too_short.status_code == 400
        assert 'Minimum stay is 2 nights' in str(too_short.data['details']['check_in'])
        assert too_long.status_code == 400
        assert 'Maximum stay is 7 nights' in str(too_long.data['details']['check_in'])

    def test_night_minimum_stay(self, stay):
        stay['days'][2].minimum_stay = 3
        stay['days'][2].save()
        response = quote(stay, 2, 4)
        assert response.status_code == 400
        assert 'must be at least 3 nights' in str(response.data['details']['availability'])

    def test_refusals_come_with_a_code_and_the_date_for_translation(self, stay):
        stay['days'][3].is_available = False
        stay['days'][3].save()
        closed = (stay['start'] + timedelta(days=3)).isoformat()
        response = quote(stay, 1, 5)
        assert response.data['reason'] == {'code': 'night_unavailable', 'params': {'date': closed}}

        stay['days'][3].is_available = True
        stay['days'][3].minimum_stay = 3
        stay['days'][3].save()
        short = quote(stay, 3, 4)
        assert short.data['reason'] == {'code': 'night_min_stay', 'params': {'date': closed, 'nights': 3}}

        stay['days'][3].minimum_stay = None
        stay['days'][3].maximum_stay = 2
        stay['days'][3].save()
        long = quote(stay, 2, 6)
        assert long.data['reason'] == {'code': 'night_max_stay', 'params': {'date': closed, 'nights': 2}}

    def test_sold_out_and_few_rooms_have_codes(self, stay):
        night = stay['start'] + timedelta(days=2)
        RoomInventory.objects.create(room_type=stay['room'], date=night, available_rooms=3, booked_rooms=3)
        sold_out = quote(stay, 1, 4)
        assert sold_out.data['reason'] == {'code': 'no_rooms_left', 'params': {'date': night.isoformat()}}

    def test_few_rooms_left_says_how_many(self, stay):
        from django.core.exceptions import ValidationError
        from bookings.pricing import refusal_reason, quote_stay
        night = stay['start'] + timedelta(days=2)
        RoomInventory.objects.create(room_type=stay['room'], date=night, available_rooms=3, booked_rooms=1)
        with pytest.raises(ValidationError) as error:
            quote_stay(stay['rate'], stay['start'] + timedelta(days=1), stay['start'] + timedelta(days=4), number_of_rooms=3)
        assert refusal_reason(error.value) == {'code': 'few_rooms_left', 'params': {'date': night.isoformat(), 'rooms': 2}}

    def test_rate_plan_min_and_max_stay_have_codes(self, stay):
        stay['rate'].min_nights = 2
        stay['rate'].max_nights = 7
        stay['rate'].save()
        assert quote(stay, 1, 2).data['reason'] == {'code': 'plan_min_stay', 'params': {'nights': 2}}
        assert quote(stay, 0, 9).data['reason'] == {'code': 'plan_max_stay', 'params': {'nights': 7}}

    def test_a_refusal_without_a_code_has_no_reason(self, stay):
        assert 'reason' not in quote(stay, 3, 3).data

    def test_bad_parameters(self, stay):
        assert quote(stay, 3, 3).status_code == 400
        other_rate = APIClient().get(f"/api/v1/properties/{stay['property'].id}/quote/", {
            'room_type_id': stay['room'].id, 'rate_plan_id': 999999,
            'check_in': stay['start'].isoformat(),
            'check_out': (stay['start'] + timedelta(days=1)).isoformat(),
        })
        assert other_rate.status_code == 400

    def test_create_booking_reports_the_same_named_date(self, stay):
        from django.core.exceptions import ValidationError
        stay['days'][3].is_available = False
        stay['days'][3].save()
        with pytest.raises(ValidationError) as error:
            Booking.create_booking(
                guest=stay['guest'], property_obj=stay['property'], room_type=stay['room'],
                rate_plan=stay['rate'], check_in=stay['start'] + timedelta(days=1),
                check_out=stay['start'] + timedelta(days=5), guest_count=1,
            )
        closed = (stay['start'] + timedelta(days=3)).isoformat()
        assert f'{closed} is not available' in str(error.value)
