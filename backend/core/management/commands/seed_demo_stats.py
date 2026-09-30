"""
DEMO DATA for the Status sections (admin and partner panels). Local development only.

    python manage.py seed_demo_stats

Creates 12 demo hotels in 3 countries (Uzbekistan, Kazakhstan, Turkey), one demo
owner account per hotel, 60 demo guests and 250 demo bookings over the last
12 months (confirmed, completed and cancelled).

- Every demo account uses a `stats-owner-NN@tickbron.demo` / `stats-guest-NN@tickbron.demo`
  address, and every demo booking's special request starts with "[DEMO]".
- All stays are in the past (check-out on or before today), so demo data never
  holds room inventory.
- Safe to run repeatedly: rows are matched by email, address and booking number
  and updated in place, dates move with today.
- Refuses to run when DEBUG is off, because the demo accounts have a well-known password.
"""
import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from bookings.models import Booking, BookingItem
from geography.mapping import GeographyIndex
from geography.models import City, Country, Region
from permissions.models import Role
from properties.models import Property, PropertyTranslation, PropertyType, RatePlan, RoomType
from users.models import User

DEMO_PASSWORD = 'DemoStats#2026'
DEMO_MARKER = '[DEMO]'
BOOKING_COUNT = 250
GUEST_COUNT = 60
SEED = 2026

# (country, region or None, city, hotel name, address, nightly price, currency)
DEMO_HOTELS = [
    ('Uzbekistan', 'Tashkent', 'Tashkent', 'Silk Road Plaza Hotel', '12 Navoi Street', '85.00', 'USD'),
    ('Uzbekistan', 'Tashkent', 'Tashkent', 'Chorsu Garden Inn', '4 Chorsu Square', '48.00', 'USD'),
    ('Uzbekistan', 'Tashkent', 'Tashkent', 'Minor Mosque View Suites', '31 Qoraqamish Street', '110.00', 'USD'),
    ('Uzbekistan', 'Samarkand', 'Samarkand', 'Registan Courtyard Hotel', '9 Tashkent Street', '70.00', 'USD'),
    ('Uzbekistan', 'Samarkand', 'Samarkand', 'Bibi-Khanym Guesthouse', '22 Islam Karimov Street', '42.00', 'USD'),
    ('Uzbekistan', 'Bukhara', 'Bukhara', 'Lyabi-Hauz Heritage Hotel', '5 Nakshbandi Street', '65.00', 'USD'),
    ('Uzbekistan', 'Bukhara', 'Bukhara', 'Ark Fortress Boutique', '17 Afrosiyob Street', '58.00', 'USD'),
    ('Kazakhstan', 'Almaty', 'Almaty', 'Medeu Mountain Lodge', '140 Dostyk Avenue', '95.00', 'USD'),
    ('Kazakhstan', 'Almaty', 'Almaty', 'Panfilov Park Hotel', '61 Panfilov Street', '72.00', 'USD'),
    ('Turkey', 'Istanbul', 'Istanbul', 'Bosphorus Terrace Hotel', '8 Kennedy Avenue', '120.00', 'EUR'),
    ('Turkey', 'Istanbul', 'Istanbul', 'Grand Bazaar Suites', '44 Divanyolu Street', '88.00', 'EUR'),
    # No region on purpose: shows the "Unspecified" group
    ('Turkey', None, 'Cappadocia', 'Cave Stone Retreat', '3 Uchisar Road', '105.00', 'EUR'),
]

# Popularity weight of each hotel above (index-aligned), so the rankings are not flat
HOTEL_WEIGHTS = [10, 6, 4, 8, 3, 7, 4, 6, 3, 5, 3, 2]

OWNER_NAMES = [
    'Akmal Karimov', 'Dilnoza Yusupova', 'Rustam Aliyev', 'Malika Rahimova', 'Jasur Tursunov',
    'Nigora Saidova', 'Bekzod Ergashev', 'Aigerim Nurlanova', 'Yerlan Sadykov', 'Mehmet Yilmaz',
    'Elif Demir', 'Can Kaya',
]
FIRST_NAMES = [
    'Aziz', 'Madina', 'Sardor', 'Gulnora', 'Timur', 'Zarina', 'Farrukh', 'Kamola', 'Otabek', 'Sevara',
    'Daniyar', 'Aruzhan', 'Ahmet', 'Zeynep', 'Anna', 'Lukas', 'Sofia', 'James', 'Mia', 'Ivan',
]
LAST_NAMES = [
    'Abdullayev', 'Nazarova', 'Kholmatov', 'Ismoilova', 'Mirzayev', 'Qodirova', 'Bekov', 'Omarova',
    'Suleimenov', 'Akhmetova', 'Ozturk', 'Celik', 'Schmidt', 'Rossi', 'Smith', 'Petrov',
]


def _owner_email(number):
    return f'stats-owner-{number:02d}@tickbron.demo'


def _guest_email(number):
    return f'stats-guest-{number:02d}@tickbron.demo'


class Command(BaseCommand):
    help = 'DEMO data for the Status sections: 12 hotels, 60 guests, 250 past bookings (DEBUG only)'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('seed_demo_stats creates demo accounts with a known password; set DEBUG=True.')

        rng = random.Random(SEED)
        # Hashed once: 72 accounts share the demo password, and hashing is slow on purpose
        self.password_hash = make_password(DEMO_PASSWORD)
        today = timezone.localdate()
        with transaction.atomic():
            owner_role, _ = Role.objects.get_or_create(
                name='hotel-owner',
                defaults={'description': 'Hotel owner role for property management', 'is_system_role': True},
            )
            hotels = self._seed_hotels(owner_role, today)
            guests = self._seed_guests(rng, today)
            summary = self._seed_bookings(rng, today, hotels, guests)
        self._print_summary(hotels, summary)

    def _demo_user(self, email, full_name, phone_number, joined, role=None):
        first_name, last_name = full_name.split(' ', 1)
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                'full_name': full_name, 'first_name': first_name, 'last_name': last_name,
                'phone_number': phone_number, 'is_active': True, 'is_staff': False,
                'is_superuser': False, 'email_verified': True, 'phone_verified': True,
                'role': role, 'date_joined': joined, 'password': self.password_hash,
            },
        )
        return user

    def _seed_hotels(self, owner_role, today):
        hotel_type, _ = PropertyType.objects.get_or_create(
            slug='hotel', defaults={'name': 'Hotel', 'description': 'Hotels and guesthouses'},
        )
        registered = timezone.make_aware(datetime.combine(today - timedelta(days=400), time(9)))
        geography = GeographyIndex(Country, Region, City)
        hotels = []
        for number, (country, region, city, name, address, price, currency) in enumerate(DEMO_HOTELS, start=1):
            owner = self._demo_user(
                _owner_email(number), OWNER_NAMES[number - 1], f'+99893560{number:04d}',
                registered - timedelta(days=number), role=owner_role,
            )
            price = Decimal(price)
            prop, _ = Property.objects.update_or_create(
                owner=owner,
                address_line1=address,
                defaults={
                    'property_type': hotel_type, 'status': 'active', 'is_active': True,
                    'max_guests': 3, 'bedrooms': 1, 'bathrooms': 1,
                    'city': city, 'state': region, 'country': country,
                    'base_price': price, 'currency': currency, 'has_wifi': True,
                    'approved_at': registered,
                },
            )
            # Geography refs from the dictionary; the hotel without a region keeps only its country
            country_ref, region_ref, city_ref = geography.match(country, region, city)
            if region is None:
                region_ref = city_ref = None
            prop.country_ref, prop.region_ref, prop.city_ref = country_ref, region_ref, city_ref
            prop.save(update_fields=['country_ref', 'region_ref', 'city_ref', 'updated_at'])
            # Back-date the registration so "since" and monthly series look real
            Property.objects.filter(pk=prop.pk).update(created_at=registered + timedelta(days=number))
            PropertyTranslation.objects.update_or_create(
                property=prop, language='en',
                defaults={'name': name, 'description': f'{DEMO_MARKER} {name} in {city}.',
                          'address_line1': address, 'city': city},
            )
            room, _ = RoomType.objects.update_or_create(
                property=prop, slug='standard-double',
                defaults={'name': 'Standard Double', 'base_occupancy': 2, 'max_occupancy': 3,
                          'base_price': price, 'currency': currency, 'total_rooms': 10,
                          'bed_configuration': '1 Double Bed'},
            )
            rate_plan, _ = RatePlan.objects.update_or_create(
                room_type=room, slug='standard',
                defaults={'name': 'Standard Rate', 'rate_type': 'standard', 'base_price': price,
                          'currency': currency, 'min_nights': 1, 'max_nights': 30, 'is_active': True},
            )
            hotels.append({'property': prop, 'name': name, 'room': room, 'rate_plan': rate_plan,
                           'price': price, 'currency': currency})
        return hotels

    def _seed_guests(self, rng, today):
        guests = []
        for number in range(1, GUEST_COUNT + 1):
            full_name = f'{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}'
            joined = timezone.make_aware(
                datetime.combine(today - timedelta(days=rng.randint(370, 420)), time(12)))
            guests.append(self._demo_user(_guest_email(number), full_name, f'+99893550{number:04d}', joined))
        return guests

    def _seed_bookings(self, rng, today, hotels, guests):
        # Some guests book much more often than others, so the users ranking is not flat
        guest_weights = [1 / (rank + 1) ** 0.7 for rank in range(len(guests))]
        statuses = {'confirmed': 0, 'completed': 0, 'cancelled': 0}
        for number in range(1, BOOKING_COUNT + 1):
            hotel = rng.choices(hotels, weights=HOTEL_WEIGHTS)[0]
            guest = rng.choices(guests, weights=guest_weights)[0]
            nights = rng.randint(1, 5)
            rooms = 2 if rng.random() < 0.15 else 1
            if number % 25 == 0:
                # A few stays that ended in the last week are still "confirmed"
                check_out = today - timedelta(days=rng.randint(0, 6))
            else:
                check_out = today - timedelta(days=rng.randint(7, 365 - nights))
            check_in = check_out - timedelta(days=nights)
            cancelled = rng.random() < 0.15
            if cancelled:
                status = 'cancelled'
            elif number % 25 == 0:
                status = 'confirmed'
            else:
                status = 'completed'
            statuses[status] += 1
            # Weekend-heavy stays and seasonal variation: +/- 20% around the hotel price
            nightly = (hotel['price'] * Decimal(str(round(rng.uniform(0.8, 1.2), 2)))).quantize(Decimal('0.01'))
            booked_at = timezone.make_aware(
                datetime.combine(check_in - timedelta(days=rng.randint(1, 45)), time(10)))

            booking, _ = Booking.objects.update_or_create(
                guest=guest,
                special_requests=f'{DEMO_MARKER} demo booking #{number:03d}',
                defaults={
                    'property': hotel['property'], 'status': status,
                    'payment_status': 'refunded' if cancelled else 'paid',
                    'check_in': check_in, 'check_out': check_out, 'number_of_nights': nights,
                    'guest_count': rng.randint(1, 3), 'number_of_rooms': rooms,
                    'total_price': nightly * nights * rooms, 'currency': hotel['currency'],
                    'guest_full_name': guest.full_name, 'guest_phone': guest.phone_number,
                    'guest_email': guest.email,
                    'cancelled_at': booked_at + timedelta(days=1) if cancelled else None,
                    'cancellation_reason': 'Demo: the guest cancelled' if cancelled else None,
                    'expires_at': None,
                },
            )
            Booking.objects.filter(pk=booking.pk).update(created_at=booked_at)
            BookingItem.objects.update_or_create(
                booking=booking,
                defaults={'room_type': hotel['room'], 'rate_plan': hotel['rate_plan'],
                          'number_of_rooms': rooms, 'price_per_night': nightly,
                          'currency': hotel['currency']},
            )
        return statuses

    def _print_summary(self, hotels, statuses):
        write = self.stdout.write
        write(self.style.SUCCESS('DEMO data for the Status sections is ready (local development only).'))
        write('')
        write(f'  {len(hotels)} demo hotels, {GUEST_COUNT} demo guests, {BOOKING_COUNT} demo bookings '
              f"({statuses['completed']} completed, {statuses['confirmed']} confirmed, "
              f"{statuses['cancelled']} cancelled), all stays in the last 12 months.")
        write('')
        write('How to see it:')
        write('  1. python manage.py seed_demo            (creates the demo super-admin)')
        write('  2. python manage.py runserver 8000       and in frontend/: npm run dev')
        write('  3. Admin: log in as admin@tickbron.demo (password DemoAdmin#2026), open /admin > Status')
        write(f'  4. Hotel owner: log in as {_owner_email(1)} (password {DEMO_PASSWORD}), open /partner > Status')
        write('')
        write('Demo hotel owners (one per hotel):')
        for number, hotel in enumerate(hotels, start=1):
            prop = hotel['property']
            region = prop.state or 'no region'
            write(f'  {_owner_email(number):<30} {hotel["name"]} ({prop.country}, {region})')
