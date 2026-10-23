"""
Owner Status v2 (.ai/PLAN_STATUS_V2.md): this month against last month, guests arriving in the next 7 days, how far
ahead guests book, repeat guests, and which room types are booked most (GET /partner/status/rooms/).
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking, BookingItem
from common.dates import business_today
from permissions.models import Role
from properties.models import Property, PropertyTranslation, PropertyType, RatePlan, RoomType
from users.models import User

P = '/api/v1/partner/status'
pytestmark = pytest.mark.django_db


def get_as(user, url, **params):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client.get(url, params)


def money(rows):
    return {row['currency']: row['amount'] for row in rows}


def first_of_month(day):
    return day.replace(day=1)


def month_start(offset):
    """First day of the month `offset` months from this one (0 = this month, -1 = last month)."""
    today = business_today()
    index = today.year * 12 + today.month - 1 + offset
    return today.replace(year=index // 12, month=index % 12 + 1, day=1)


@pytest.fixture
def world(db):
    role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
    owner = User.objects.create_user(email='own@example.com', password='OwnerPassword#123', role=role, phone_number='+998901110001')
    other = User.objects.create_user(
        email='oth@example.com', password='OwnerPassword#123', role=role, phone_number='+998901110002')
    hotel_type = PropertyType.objects.create(name='Hotel', slug='hotel')

    def hotel(who, name):
        prop = Property.objects.create(
            owner=who, property_type=hotel_type, status='active', max_guests=2, address_line1=f'1 {name} St',
            city='Tashkent', country='Uzbekistan', base_price=Decimal('50.00'), currency='USD')
        PropertyTranslation.objects.create(property=prop, language='en', name=name)
        return prop

    def room(prop, name, rooms):
        kind = RoomType.objects.create(property=prop, name=name, slug=name.lower(), base_occupancy=2, max_occupancy=2,
                                       base_price=Decimal('50.00'), currency='USD', total_rooms=rooms)
        plan = RatePlan.objects.create(room_type=kind, name='Std', slug=f'std-{name.lower()}', rate_type='standard',
                                       base_price=Decimal('50.00'), currency='USD', min_nights=1, is_active=True)
        return kind, plan

    alpha, beta, foreign = hotel(owner, 'Alpha'), hotel(owner, 'Beta'), hotel(other, 'Foreign')
    guests = [User.objects.create_user(email=f'g{n}@example.com', password='GuestPassword#123', phone_number=f'+99890333000{n}')
              for n in range(1, 5)]
    return {
        'owner': owner, 'other': other, 'alpha': alpha, 'beta': beta, 'foreign': foreign, 'guests': guests,
        'standard': room(alpha, 'Standard', 5), 'suite': room(alpha, 'Suite', 2), 'double': room(beta, 'Double', 3),
        'foreign_room': room(foreign, 'Other', 4), 'hotel_type': hotel_type,
    }


def book(world, guest, prop, check_in, kind, nights=2, status='confirmed', rooms=1, guests=2, price='100.00'):
    """A booking with one item of `kind` (a (room type, rate plan) pair); total = price per night * nights * rooms."""
    room_type, plan = world[kind] if isinstance(kind, str) else kind
    booking = Booking.objects.create(
        guest=guest, property=prop, status=status, payment_status='paid', check_in=check_in,
        check_out=check_in + timedelta(days=nights), number_of_nights=nights, number_of_rooms=rooms, guest_count=guests,
        total_price=Decimal(price) * nights * rooms, currency='USD', guest_full_name='G', guest_email=guest.email,
        expires_at=None)
    BookingItem.objects.create(booking=booking, room_type=room_type, rate_plan=plan, number_of_rooms=rooms,
                               price_per_night=Decimal(price), currency='USD')
    return booking


class TestMonthComparison:
    def test_this_month_against_last_month(self, world):
        g, alpha = world['guests'], world['alpha']
        book(world, g[0], alpha, month_start(0), 'standard', status='completed', price='100.00', guests=2)   # 200
        book(world, g[1], alpha, month_start(0), 'standard', status='completed', price='50.00', guests=3)    # 100
        book(world, g[0], alpha, month_start(-1), 'standard', status='completed', price='100.00', guests=2)  # 200
        book(world, g[2], alpha, month_start(-2), 'standard', status='completed', price='999.00')            # older: not in it
        book(world, g[3], world['foreign'], month_start(0), 'foreign_room', status='completed')              # not mine
        months = get_as(world['owner'], f'{P}/').data['months']
        assert (months['current']['month'], months['previous']['month']) == (
            month_start(0).strftime('%Y-%m'), month_start(-1).strftime('%Y-%m'))
        current = months['current']
        assert (current['bookings'], current['guests'], money(current['revenue'])) == (2, 5, {'USD': '300.00'})
        previous = months['previous']
        assert (previous['bookings'], previous['guests'], money(previous['revenue'])) == (1, 2, {'USD': '200.00'})
        assert months['change_pct']['bookings'] == '100.0'
        assert months['change_pct']['guests'] == '150.0'
        assert months['change_pct']['revenue'] == [{'currency': 'USD', 'pct': '50.0'}]

    def test_no_percent_when_last_month_was_empty(self, world):
        book(world, world['guests'][0], world['alpha'], month_start(0), 'standard', status='completed')
        months = get_as(world['owner'], f'{P}/').data['months']
        assert months['previous']['bookings'] == 0
        assert months['change_pct']['bookings'] is None
        assert months['change_pct']['revenue'] == [{'currency': 'USD', 'pct': None}]

    def test_the_selected_period_does_not_change_it(self, world):
        book(world, world['guests'][0], world['alpha'], month_start(0), 'standard', status='completed')
        data = get_as(world['owner'], f'{P}/', period='2020').data
        assert data['totals']['bookings'] == 0
        assert data['months']['current']['bookings'] == 1

    def test_guests_arriving_in_the_next_seven_days(self, world):
        today, g, alpha = business_today(), world['guests'], world['alpha']
        book(world, g[0], alpha, today, 'standard', guests=2)                                   # today counts
        book(world, g[1], alpha, today + timedelta(days=6), 'standard', guests=3)               # day 7 counts
        book(world, g[2], alpha, today + timedelta(days=7), 'standard', guests=4)               # day 8 does not
        book(world, g[2], alpha, today + timedelta(days=2), 'standard', status='cancelled')     # cancelled does not
        book(world, g[3], world['foreign'], today + timedelta(days=1), 'foreign_room')          # not mine
        soon = get_as(world['owner'], f'{P}/').data['months']['next_7_days']
        assert soon == {'bookings': 2, 'guests': 5}


class TestInsightAdditions:
    def test_average_lead_days_and_repeat_guests(self, world):
        today, g, alpha = business_today(), world['guests'], world['alpha']
        book(world, g[0], alpha, today + timedelta(days=10), 'standard')   # booked today: 10 days ahead
        book(world, g[0], alpha, today + timedelta(days=20), 'standard')   # 20 days ahead
        book(world, g[1], alpha, today + timedelta(days=30), 'standard')   # 30 days ahead
        insights = get_as(world['owner'], f'{P}/').data['insights']
        assert insights['average_lead_days'] == '20.0'
        assert insights['repeat_guest_pct'] == '50.00'   # one of the two guests came twice

    def test_a_booking_made_earlier_counts_its_real_lead(self, world):
        booking = book(world, world['guests'][0], world['alpha'], business_today() + timedelta(days=10), 'standard')
        Booking.objects.filter(pk=booking.pk).update(created_at=timezone.now() - timedelta(days=5))
        assert get_as(world['owner'], f'{P}/').data['insights']['average_lead_days'] == '15.0'

    def test_empty_owner_has_no_rates(self, world):
        insights = get_as(world['owner'], f'{P}/').data['insights']
        assert insights['average_lead_days'] is None
        assert insights['repeat_guest_pct'] is None


class TestRooms:
    def rows(self, world, **params):
        response = get_as(world['owner'], f'{P}/rooms/', **params)
        assert response.status_code == 200, response.data
        return {row['name']: row for row in response.data['rows']}, response.data

    def test_the_busiest_room_type_comes_first_with_every_room_type_listed(self, world):
        g, alpha, beta = world['guests'], world['alpha'], world['beta']
        for guest in (g[0], g[1], g[2]):
            book(world, guest, alpha, month_start(0), 'standard', nights=2)
        book(world, g[0], alpha, month_start(0), 'suite', nights=3, status='completed', price='300.00')
        book(world, g[1], beta, month_start(0), 'double', nights=1, rooms=2, status='completed', price='80.00')
        book(world, g[1], alpha, month_start(0), 'standard', status='cancelled')   # not counted
        book(world, g[2], world['foreign'], month_start(0), 'foreign_room')        # not mine
        response = get_as(world['owner'], f'{P}/rooms/')
        names = [row['name'] for row in response.data['rows']]
        # 3, 1 and 1 bookings; the tie goes to the room type with more room nights (Suite 3, Double 2)
        assert names == ['Standard', 'Suite', 'Double']
        assert set(names) == {'Standard', 'Suite', 'Double'}
        assert 'Other' not in names

    def test_numbers_per_room_type(self, world):
        g, alpha, beta = world['guests'], world['alpha'], world['beta']
        book(world, g[0], alpha, month_start(0), 'standard', nights=2)                       # counted, no revenue yet
        book(world, g[1], alpha, month_start(0), 'standard', nights=3, rooms=2, status='completed', price='60.00')
        book(world, g[0], alpha, month_start(0), 'suite', nights=1, status='completed', price='300.00')
        book(world, g[2], beta, month_start(0), 'double', nights=1, rooms=1, status='completed', price='80.00')
        rows, data = self.rows(world)
        standard, suite, double = rows['Standard'], rows['Suite'], rows['Double']
        assert (standard['bookings'], standard['room_nights'], money(standard['revenue'])) == (2, 2 + 6, {'USD': '360.00'})
        assert (suite['bookings'], suite['room_nights'], money(suite['revenue'])) == (1, 1, {'USD': '300.00'})
        assert (double['bookings'], double['room_nights'], money(double['revenue'])) == (1, 1, {'USD': '80.00'})
        assert (standard['property']['name'], double['property']['name']) == ('Alpha', 'Beta')
        assert (standard['share_pct'], suite['share_pct'], double['share_pct']) == ('50.00', '25.00', '25.00')
        assert (standard['total_rooms'], suite['total_rooms'], double['total_rooms']) == (5, 2, 3)

    def test_a_room_type_nobody_booked_is_listed_with_zeros(self, world):
        rows, _ = self.rows(world)
        assert rows['Suite']['bookings'] == 0 and rows['Suite']['revenue'] == []
        assert rows['Suite']['share_pct'] is None

    def test_occupancy_needs_a_bounded_period(self, world):
        book(world, world['guests'][0], world['alpha'], month_start(0), 'standard', nights=2, rooms=1)
        month = month_start(0).strftime('%Y-%m')
        rows, data = self.rows(world, period=month)
        days = (month_start(1) - month_start(0)).days
        assert rows['Standard']['occupancy_rate'] == f'{Decimal(2) * 100 / (5 * days):.2f}'
        rows, _ = self.rows(world)
        assert rows['Standard']['occupancy_rate'] is None

    def test_a_booking_of_two_room_types_counts_for_both(self, world):
        g, alpha = world['guests'], world['alpha']
        booking = book(world, g[0], alpha, month_start(0), 'standard', nights=2, price='50.00')
        suite, plan = world['suite']
        BookingItem.objects.create(
            booking=booking, room_type=suite, rate_plan=plan, number_of_rooms=1, price_per_night=Decimal('150.00'),
            currency='USD')
        rows, _ = self.rows(world)
        assert rows['Standard']['bookings'] == 1 and rows['Suite']['bookings'] == 1

    def test_one_hotel_only(self, world):
        book(world, world['guests'][0], world['alpha'], month_start(0), 'standard')
        book(world, world['guests'][1], world['beta'], month_start(0), 'double')
        rows, data = self.rows(world, property=world['beta'].id)
        assert set(rows) == {'Double'}

    def test_access_and_bad_input(self, world):
        url = f'{P}/rooms/'
        assert get_as(world['owner'], url, property=world['foreign'].id).status_code == 404
        assert get_as(world['owner'], url, property='x').status_code == 400
        assert get_as(world['owner'], url, period='nonsense').status_code == 400
        assert get_as(world['guests'][0], url).status_code == 403
        assert get_as(None, url).status_code in (401, 403)

    def test_another_owner_sees_only_own_rooms(self, world):
        book(world, world['guests'][0], world['alpha'], month_start(0), 'standard')
        rows, _ = {row['name']: row for row in get_as(world['other'], f'{P}/rooms/').data['rows']}, None
        assert set(rows) == {'Other'}
