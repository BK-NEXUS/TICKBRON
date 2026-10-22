"""
Tests for seed_demo_stats: DEMO data for the Status sections (local development only).
"""
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.utils import timezone

from bookings.models import Booking, BookingItem
from properties.models import Property, RoomInventory
from users.models import User

GUEST_EMAILS = 'stats-guest-'
OWNER_EMAILS = 'stats-owner-'


def run_seed():
    out = StringIO()
    call_command('seed_demo_stats', stdout=out)
    return out.getvalue()


def demo_bookings():
    return Booking.objects.filter(guest__email__startswith=GUEST_EMAILS)


def demo_hotels():
    return Property.objects.filter(owner__email__startswith=OWNER_EMAILS)


@pytest.mark.django_db
class TestSeedDemoStats:
    @pytest.fixture(autouse=True)
    def debug_on(self, settings):
        settings.DEBUG = True

    def test_every_hotel_is_on_the_map_near_its_city_and_no_two_pins_overlap(self):
        run_seed()

        hotels = list(demo_hotels())
        assert all(h.latitude is not None and h.longitude is not None for h in hotels)
        assert all(-90 <= h.latitude <= 90 and -180 <= h.longitude <= 180 for h in hotels)
        assert len({(h.latitude, h.longitude) for h in hotels}) == len(hotels)
        tashkent = [h for h in hotels if h.city == 'Tashkent']
        assert all(abs(float(h.latitude) - 41.31) < 0.2 and abs(float(h.longitude) - 69.28) < 0.2 for h in tashkent)

    def test_running_twice_keeps_the_same_coordinates(self):
        run_seed()
        first = {h.pk: (h.latitude, h.longitude) for h in demo_hotels()}
        run_seed()
        assert {h.pk: (h.latitude, h.longitude) for h in demo_hotels()} == first

    def test_refuses_to_run_without_debug(self, settings):
        settings.DEBUG = False
        with pytest.raises(CommandError):
            run_seed()
        assert not demo_hotels().exists()

    def test_creates_hotels_in_three_countries_with_owner_accounts(self):
        run_seed()

        hotels = demo_hotels()
        assert hotels.count() == 12
        assert set(hotels.values_list('country', flat=True)) == {'Uzbekistan', 'Kazakhstan', 'Turkey'}
        regions = set(hotels.exclude(state__isnull=True).exclude(state='').values_list('state', flat=True))
        assert len(regions) >= 4
        # At least one hotel has no region, so the "Unspecified" group shows up
        assert hotels.filter(state__isnull=True).exists()
        assert all(h.owner.role.name == 'hotel-owner' for h in hotels.select_related('owner__role'))
        assert hotels.values('owner').distinct().count() == 12
        assert all(h.translations.filter(language='en').exists() for h in hotels)
        # Geography refs: every hotel has its country; the one without a region has no region or city
        assert not hotels.filter(country_ref__isnull=True).exists()
        no_region = hotels.get(state__isnull=True)
        assert (no_region.country_ref.code, no_region.region_ref, no_region.city_ref) == ('TR', None, None)
        silk = hotels.select_related('region_ref', 'city_ref').get(translations__name='Silk Road Plaza Hotel')
        assert (silk.region_ref.name_en, silk.city_ref.name_en) == ('Tashkent', 'Tashkent')
        assert hotels.exclude(pk=no_region.pk).filter(city_ref__isnull=True).count() == 0
        # The printed demo password works
        assert User.objects.get(email='stats-owner-01@tickbron.demo').check_password('DemoStats#2026')
        assert User.objects.get(email='stats-guest-60@tickbron.demo').check_password('DemoStats#2026')

    def test_creates_60_guests_and_250_past_bookings(self):
        run_seed()

        assert User.objects.filter(email__startswith=GUEST_EMAILS).count() == 60
        bookings = demo_bookings()
        assert bookings.count() == 250
        assert set(bookings.values_list('status', flat=True)) == {'confirmed', 'completed', 'cancelled'}

        today = timezone.localdate()
        for booking in bookings.select_related('property'):
            # Past stays only, so no room inventory is held by demo data
            assert booking.check_out <= today
            assert booking.check_in >= today - timedelta(days=365)
            assert booking.number_of_nights == (booking.check_out - booking.check_in).days
            assert booking.total_price > 0
            assert booking.currency == booking.property.currency
        assert BookingItem.objects.filter(booking__in=bookings).count() == 250

    def test_uses_more_than_one_currency(self):
        run_seed()
        assert demo_bookings().values('currency').distinct().count() >= 2

    def test_does_not_touch_room_inventory(self):
        before = RoomInventory.objects.count()
        run_seed()
        assert RoomInventory.objects.count() == before

    def test_running_twice_does_not_duplicate(self):
        run_seed()
        counts = (User.objects.count(), Property.objects.count(), Booking.objects.count(),
                  BookingItem.objects.count())
        codes = set(demo_bookings().values_list('confirmation_code', flat=True))

        run_seed()

        assert (User.objects.count(), Property.objects.count(), Booking.objects.count(),
                BookingItem.objects.count()) == counts
        assert set(demo_bookings().values_list('confirmation_code', flat=True)) == codes

    def test_prints_how_to_use_it(self):
        output = run_seed()
        assert 'DEMO' in output
        assert 'stats-owner-01@tickbron.demo' in output
        assert '/admin' in output


@pytest.mark.django_db
class TestSeedDemoStatsCash:
    """Cash at the hotel: demo bookings carry no payment rows and are paid at the hotel."""

    @pytest.fixture(autouse=True)
    def debug_on(self, settings):
        settings.DEBUG = True

    def test_demo_bookings_have_no_payments(self):
        from payments.models import PaymentTransaction

        run_seed()

        bookings = demo_bookings()
        assert not PaymentTransaction.objects.filter(booking__in=bookings).exists()
        assert set(bookings.values_list('payment_status', flat=True)) == {'pending'}


@pytest.mark.django_db
class TestSeedDemoPromotions:
    @pytest.fixture(autouse=True)
    def debug_on(self, settings):
        settings.DEBUG = True

    def test_seeds_running_unpaid_and_expired_promotions_with_numbers(self):
        from promotions import service
        from promotions.models import Promotion, PromotionDailyStat

        run_seed()

        assert Promotion.objects.count() == 7
        shown = service.shown_now()
        assert shown.count() == 5
        assert Promotion.objects.filter(paid_at__isnull=True).count() == 1
        assert Promotion.objects.filter(status='ended').count() == 1
        assert PromotionDailyStat.objects.filter(promotion__in=shown, clicks__gt=0).exists()

    def test_rerun_does_not_duplicate_promotions(self):
        from promotions.models import Promotion

        run_seed()
        run_seed()

        assert Promotion.objects.count() == 7
