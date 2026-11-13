"""
Bron status ótiwleri ushın haqıyqıy birdey waqıtlılıq testleri (audit #18).

Bular PostgreSQL talap etedi: SQLite te qatar dárejesindegi qulıplar joq hám jazıwshılardı izbe-iz etedi,
sol sebepli jarıslar onda bolıp bolmaydı. .env degi PostgreSQL sazlamaları menen isletiń:

    pytest --create-db bookings/tests/test_concurrency.py
"""
import threading
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TransactionTestCase
from django.utils import timezone

from bookings.models import Booking
from properties.models import DateInventory, Property, PropertyType, RatePlan, RoomInventory, RoomType
from users.models import User
from currency.testing import make_usd_rate


def run_concurrently(*calls):
    """
    Hár shaqırıwdı birdey waqıtta óz thread inde hám DB ulanıwında baslaw.

    Hár shaqırıw ushın bir ('ok', result) yamasa ('error', exception) tuple qaytaradı.
    """
    barrier = threading.Barrier(len(calls))
    results = [None] * len(calls)

    def worker(index, call):
        try:
            barrier.wait(timeout=10)
            results[index] = ('ok', call())
        except Exception as exc:  # test jıynap tekseredi
            results[index] = ('error', exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(i, call)) for i, call in enumerate(calls)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert all(not thread.is_alive() for thread in threads), 'a worker thread hung (deadlock?)'
    return results


class BookingConcurrencyTests(TransactionTestCase):
    """Eki soraw birdey waqıtta bir bronǵa háreket etedi."""

    def setUp(self):
        make_usd_rate()  # R6: USD mehmanxanasın tek kurs bar bolǵanda bronlap boladı

        self.user = User.objects.create_user(phone_number='+998901112233', email='race@example.com', password='testpass123')
        property_type = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.property = Property.objects.create(
            owner=self.user, property_type=property_type, status='active',
            max_guests=4, bedrooms=1, bathrooms=1, city='Tashkent', country='Uzbekistan',
            base_price=Decimal('100.00'), currency='USD'
        )
        self.room_type = RoomType.objects.create(
            property=self.property, name='Standard', slug='standard', base_occupancy=2,
            max_occupancy=4, base_price=Decimal('100.00'), currency='USD', total_rooms=5
        )
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type, name='Standard Rate', slug='standard-rate', rate_type='standard',
            base_price=Decimal('100.00'), currency='USD', min_nights=1, max_nights=30, is_active=True
        )
        self.day = timezone.localdate() + timedelta(days=5)
        self.inventory = DateInventory.objects.create(
            rate_plan=self.rate_plan, date=self.day, available_rooms=5, booked_rooms=0,
            price=Decimal('100.00'), currency='USD', is_available=True
        )
        # Eki bron túndi ustap turadı, sol sebepli qos bosatıw booked_rooms >= 0 check constraint in buzbastan
        # 0 retinde kórinedi
        self.other_booking = self._book()
        self.booking = self._book()
        # RoomInventory xona sanın sistema basqaratuǵın hám jańalaytuǵın qatar (audit
        # #31); joqarıdaǵı birinshi _book() shaqırıwı bul qatardı jaratqan (ádetde: total_rooms)
        self.room_inventory = RoomInventory.objects.get(room_type=self.room_type, date=self.day)
        assert self._booked_rooms() == 2

    def _book(self):
        return Booking.create_booking(
            guest=self.user, property_obj=self.property, room_type=self.room_type, rate_plan=self.rate_plan,
            check_in=self.day, check_out=self.day + timedelta(days=1), guest_count=2
        )

    def _booked_rooms(self):
        return RoomInventory.objects.get(pk=self.room_inventory.pk).booked_rooms

    def _stale_copies(self, count=2):
        """Jarıstan aldın júklengen ǵárezsiz jaddaǵı nusqalar, eki soraw alǵanday."""
        return [Booking.objects.get(pk=self.booking.pk) for _ in range(count)]

    @staticmethod
    def _outcomes(results):
        return sorted(kind for kind, _ in results)

    def _assert_losers_got_validation_errors(self, results):
        for kind, value in results:
            if kind == 'error':
                assert isinstance(value, ValidationError), repr(value)

    def test_double_cancel_releases_inventory_once(self):
        first, second = self._stale_copies()

        results = run_concurrently(first.cancel_booking, second.cancel_booking)

        assert self._outcomes(results) == ['error', 'ok']
        self._assert_losers_got_validation_errors(results)
        assert self._booked_rooms() == 1
        assert Booking.objects.get(pk=self.booking.pk).status == 'cancelled'

    def test_cancel_and_expire_release_inventory_once(self):
        to_cancel, to_expire = self._stale_copies()

        results = run_concurrently(to_cancel.cancel_booking, to_expire.expire_booking)

        assert self._outcomes(results) == ['error', 'ok']
        self._assert_losers_got_validation_errors(results)
        assert self._booked_rooms() == 1

    def test_last_room_cannot_be_sold_twice(self):
        RoomInventory.objects.filter(pk=self.room_inventory.pk).update(available_rooms=3)  # 2 ustap tur, 1 qaldı

        results = run_concurrently(self._book, self._book)

        assert self._outcomes(results) == ['error', 'ok']
        self._assert_losers_got_validation_errors(results)
        assert self._booked_rooms() == 3


class RoomInventoryConcurrencyTests(TransactionTestCase):
    """
    Fizikalıq xona óz xona túriniń hár rate plan ı ortaq paydalanatuǵın bir RoomInventory
    qatarı (audit #31): sońǵı bir xona ushın jarısatuǵın eki rate plan ekewi de
    jeńip ketpewi kerek.
    """

    def setUp(self):
        make_usd_rate()  # R6: USD mehmanxanasın tek kurs bar bolǵanda bronlap boladı

        self.user = User.objects.create_user(phone_number='+998901112233', email='race-two-rate-plans@example.com', password='testpass123')
        property_type = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.property = Property.objects.create(
            owner=self.user, property_type=property_type, status='active',
            max_guests=4, bedrooms=1, bathrooms=1, city='Tashkent', country='Uzbekistan',
            base_price=Decimal('100.00'), currency='USD'
        )
        # Bir fizikalıq xona, eki rate plan arqalı satılatuǵın (audit #31 qaytalaw)
        self.room_type = RoomType.objects.create(
            property=self.property, name='Standard', slug='standard', base_occupancy=2,
            max_occupancy=4, base_price=Decimal('100.00'), currency='USD', total_rooms=1
        )
        self.flexible = RatePlan.objects.create(
            room_type=self.room_type, name='Flexible', slug='flexible', rate_type='standard',
            base_price=Decimal('100.00'), currency='USD', min_nights=1, max_nights=30, is_active=True
        )
        self.non_refundable = RatePlan.objects.create(
            room_type=self.room_type, name='Non-refundable', slug='non-refundable',
            rate_type='non_refundable', base_price=Decimal('90.00'), currency='USD',
            min_nights=1, max_nights=30, is_active=True
        )
        self.day = timezone.localdate() + timedelta(days=5)
        for rate_plan in (self.flexible, self.non_refundable):
            DateInventory.objects.create(
                rate_plan=rate_plan, date=self.day, available_rooms=1, booked_rooms=0,
                price=rate_plan.base_price, currency='USD', is_available=True
            )

    def _book(self, rate_plan):
        return Booking.create_booking(
            guest=self.user, property_obj=self.property, room_type=self.room_type, rate_plan=rate_plan,
            check_in=self.day, check_out=self.day + timedelta(days=1), guest_count=2
        )

    def test_last_room_cannot_be_sold_through_two_rate_plans_at_once(self):
        results = run_concurrently(
            lambda: self._book(self.flexible), lambda: self._book(self.non_refundable),
        )

        assert sorted(kind for kind, _ in results) == ['error', 'ok']
        for kind, value in results:
            if kind == 'error':
                assert isinstance(value, ValidationError), repr(value)
        room_inventory = RoomInventory.objects.get(room_type=self.room_type, date=self.day)
        assert room_inventory.booked_rooms == 1
        assert Booking.objects.filter(status='pending').count() == 1


class PendingCapRaceTests(TransactionTestCase):
    """A06-3: bir akkauntıń paralel sorawları kútip turǵan bron tekseriwinen hámmesi ótip ala almaydı."""

    def setUp(self):
        make_usd_rate()
        self.user = User.objects.create_user(phone_number='+998901112233', email='holder@example.com', password='testpass123')
        property_type = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.property = Property.objects.create(
            owner=self.user, property_type=property_type, status='active',
            max_guests=4, bedrooms=1, bathrooms=1, city='Tashkent', country='Uzbekistan',
            base_price=Decimal('100.00'), currency='USD'
        )
        self.room_type = RoomType.objects.create(
            property=self.property, name='Standard', slug='standard', base_occupancy=2,
            max_occupancy=4, base_price=Decimal('100.00'), currency='USD', total_rooms=50
        )
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type, name='Standard Rate', slug='standard-rate', rate_type='standard',
            base_price=Decimal('100.00'), currency='USD', min_nights=1, max_nights=30, is_active=True
        )
        self.check_in = timezone.localdate() + timedelta(days=5)
        for offset in range(8):
            day = self.check_in + timedelta(days=offset)
            DateInventory.objects.create(rate_plan=self.rate_plan, date=day, available_rooms=50, booked_rooms=0,
                                         price=Decimal('100.00'), currency='USD', is_available=True)
            RoomInventory.objects.create(room_type=self.room_type, date=day, available_rooms=50, booked_rooms=0,
                                         is_available=True)

    def book_nights(self, first_night, nights=1):
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(self.user)
        check_in = self.check_in + timedelta(days=first_night)
        return client.post('/api/v1/bookings/', {
            'property_id': self.property.id, 'room_type_id': self.room_type.id,
            'rate_plan_id': self.rate_plan.id, 'check_in': check_in.isoformat(),
            'check_out': (check_in + timedelta(days=nights)).isoformat(), 'guest_count': 1, 'expected_arrival_time': '14:00',
        }, format='json').status_code

    def test_parallel_creates_never_exceed_the_cap(self):
        from bookings.views import MAX_UPCOMING_BOOKINGS_PER_GUEST  # MAX_PENDING_BOOKINGS_PER_GUEST edi

        # segiz túrli tún, sol sebepli tek shek (kesilisiw qaǵıydası emes) olardı biykar ete aladı
        results = run_concurrently(*[lambda night=night: self.book_nights(night) for night in range(8)])

        assert [r for r in results if r[0] == 'error'] == []
        upcoming = Booking.objects.filter(guest=self.user, status='confirmed').count()  # bronlar birden tastıyıqlanadı
        assert upcoming == MAX_UPCOMING_BOOKINGS_PER_GUEST, [r[1] for r in results]

    def test_parallel_creates_for_the_same_nights_book_them_once(self):
        results = run_concurrently(*[lambda: self.book_nights(0, nights=2)] * 6)

        assert [r for r in results if r[0] == 'error'] == []
        assert Booking.objects.filter(guest=self.user, status='confirmed').count() == 1, [r[1] for r in results]
