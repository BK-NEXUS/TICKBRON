"""
DEMO DATA at volume, for measuring performance (R14). Local development only.

    python manage.py seed_demo_bulk --hotels 2000 --guests 300 --bookings 10000 --days 90

Run it against a scratch database (DB_NAME=tickbron_perf): it creates thousands of rows.
Hotels get 2 room types, 2 rate plans each, 3 photos, 6 amenities, 3 languages of names and
`--days` days of inventory; bookings are spread over the next and last months.

- Every account is `bulk-owner-NNNN@tickbron.demo` / `bulk-guest-NNNN@tickbron.demo`, marker "[BULK]".
- Refuses to run when DEBUG is off, and when bulk data already exists.
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from bookings.models import Booking, BookingItem
from common.dates import business_today
from geography.mapping import GeographyIndex
from geography.models import City, Country, Region
from permissions.models import Role
from properties.models import (
    Amenity, AmenityCategory, DateInventory, Property, PropertyAmenity, PropertyPhoto,
    PropertyTranslation, PropertyType, RatePlan, RoomInventory, RoomType,
)
from users.models import User

MARKER = '[BULK]'
PASSWORD = 'DemoBulk#2026'
SEED = 12
CITIES = [
    ('Uzbekistan', 'Tashkent', 'Tashkent', 'UZS'), ('Uzbekistan', 'Samarkand', 'Samarkand', 'UZS'),
    ('Uzbekistan', 'Bukhara', 'Bukhara', 'UZS'), ('Uzbekistan', 'Khorezm', 'Khiva', 'UZS'),
    ('Uzbekistan', 'Fergana', 'Fergana', 'UZS'), ('Uzbekistan', 'Namangan', 'Namangan', 'UZS'),
    ('Kazakhstan', 'Almaty', 'Almaty', 'USD'), ('Turkey', 'Istanbul', 'Istanbul', 'USD'),
]
WORDS = ['Silk', 'Road', 'Golden', 'Garden', 'Registan', 'Chorsu', 'Minor', 'Grand', 'Old', 'Town', 'Palace',
         'Plaza', 'Courtyard', 'Heritage', 'Boutique', 'Lyabi', 'Hauz', 'Ark', 'Fortress', 'Oasis']
AMENITIES = ['WiFi', 'Air conditioning', 'Breakfast', 'Parking', 'Pool', 'Airport shuttle', 'Gym', 'Spa',
             'Restaurant', 'Laundry', 'Garden', 'Family rooms']


class Command(BaseCommand):
    help = 'Create demo data at volume for performance measurements (DEBUG only, scratch database)'

    def add_arguments(self, parser):
        parser.add_argument('--hotels', type=int, default=2000)
        parser.add_argument('--guests', type=int, default=300)
        parser.add_argument('--bookings', type=int, default=10000)
        parser.add_argument('--days', type=int, default=90)

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('seed_demo_bulk creates demo accounts with a known password; set DEBUG=True.')
        if User.objects.filter(email__startswith='bulk-owner-').exists():
            raise CommandError('Bulk demo data already exists in this database.')
        rng = random.Random(SEED)
        with transaction.atomic():
            hotels = self._hotels(rng, options['hotels'], options['days'])
            guests = self._guests(options['guests'])
            self._bookings(rng, hotels, guests, options['bookings'])
        self.stdout.write(self.style.SUCCESS(
            f"Created {options['hotels']} hotels, {len(guests)} guests, {options['bookings']} bookings."))

    def _users(self, prefix, count, phone_prefix, role=None):
        password = make_password(PASSWORD)
        rows = [User(
            email=f'{prefix}-{n:04d}@tickbron.demo', full_name=f'Bulk {prefix} {n}', password=password,
            phone_number=f'{phone_prefix}{n:05d}', role=role, is_active=True,
        ) for n in range(1, count + 1)]
        User.objects.bulk_create(rows, batch_size=500)
        return list(User.objects.filter(email__startswith=f'{prefix}-').order_by('id'))

    def _guests(self, count):
        return self._users('bulk-guest', count, '+9989')

    def _hotels(self, rng, count, days):
        today = business_today()
        owner_role = Role.objects.get_or_create(name='hotel-owner', defaults={'description': 'Hotel owner'})[0]
        owners = self._users('bulk-owner', max(1, count // 10), '+9988', role=owner_role)
        hotel_type = PropertyType.objects.get_or_create(slug='hotel', defaults={'name': 'Hotel'})[0]
        category = AmenityCategory.objects.get_or_create(slug='bulk', defaults={'name': 'Bulk'})[0]
        amenities = [Amenity.objects.get_or_create(
            slug=name.lower().replace(' ', '-'), defaults={'name': name, 'category': category, 'is_searchable': True})[0]
            for name in AMENITIES]
        geography = GeographyIndex(Country, Region, City)
        refs = {city: geography.match(country, region, city) for country, region, city, _ in CITIES}

        properties = []
        for n in range(count):
            country, region, city, currency = CITIES[n % len(CITIES)]
            price = Decimal(rng.randrange(40, 160, 5)) if currency == 'USD' else Decimal(rng.randrange(300, 1500, 25) * 1000)
            country_ref, region_ref, city_ref = refs[city]
            properties.append(Property(
                owner=owners[n % len(owners)], property_type=hotel_type, status='active', is_active=True,
                max_guests=3, bedrooms=1, bathrooms=1, address_line1=f'{n + 1} {rng.choice(WORDS)} Street',
                city=city, state=region, country=country, base_price=price, currency=currency,
                has_wifi=True, approved_at=timezone.now(),
                country_ref=country_ref, region_ref=region_ref, city_ref=city_ref,
            ))
        Property.objects.bulk_create(properties, batch_size=500)
        created = list(Property.objects.filter(address_line1__regex=r'^\d+ \w+ Street$', owner__in=owners).order_by('id'))

        translations, photos, links, rooms = [], [], [], []
        for prop in created:
            name = f'{rng.choice(WORDS)} {rng.choice(WORDS)} {prop.city} Hotel'
            for language in ('en', 'ru', 'uz'):
                translations.append(PropertyTranslation(
                    property=prop, language=language, name=name,
                    description=f'{MARKER} {name} in {prop.city}.', address_line1=prop.address_line1, city=prop.city))
            for index in range(3):
                photos.append(PropertyPhoto(property=prop, photo=f'properties/{prop.id}/photos/{index}.jpg',
                                            photo_type='exterior', is_primary=index == 0, display_order=index))
            for amenity in rng.sample(amenities, 6):
                links.append(PropertyAmenity(property=prop, amenity=amenity, is_available=True))
            for room_name, slug, extra in (('Standard Double', 'standard-double', Decimal('1')),
                                           ('Deluxe King', 'deluxe-king', Decimal('1.4'))):
                rooms.append(RoomType(
                    property=prop, name=room_name, slug=slug, base_occupancy=2, max_occupancy=3,
                    base_price=prop.base_price * extra, currency=prop.currency, total_rooms=8,
                    bed_configuration='1 Double Bed'))
        PropertyTranslation.objects.bulk_create(translations, batch_size=2000)
        PropertyPhoto.objects.bulk_create(photos, batch_size=2000)
        PropertyAmenity.objects.bulk_create(links, batch_size=2000)
        RoomType.objects.bulk_create(rooms, batch_size=2000)

        room_types = list(RoomType.objects.filter(property__in=created).select_related('property').order_by('id'))
        plans = []
        for room in room_types:
            for plan_name, slug, discount in (('Standard Rate', 'standard', Decimal('1')),
                                              ('Non-refundable Rate', 'non-refundable', Decimal('0.9'))):
                plans.append(RatePlan(room_type=room, name=plan_name, slug=slug, rate_type='standard',
                                      base_price=room.base_price * discount, currency=room.currency,
                                      min_nights=1, max_nights=30, is_active=True))
        RatePlan.objects.bulk_create(plans, batch_size=2000)

        date_rows, room_rows = [], []
        for room in room_types:
            for offset in range(days):
                room_rows.append(RoomInventory(room_type=room, date=today + timedelta(days=offset),
                                               available_rooms=8, booked_rooms=0, is_available=True))
        for plan in RatePlan.objects.filter(room_type__in=room_types):
            for offset in range(days):
                date_rows.append(DateInventory(rate_plan=plan, date=today + timedelta(days=offset),
                                               available_rooms=8, booked_rooms=0, price=plan.base_price,
                                               currency=plan.currency, is_available=True))
        RoomInventory.objects.bulk_create(room_rows, batch_size=5000)
        DateInventory.objects.bulk_create(date_rows, batch_size=5000)

        plan_by_room = {}
        for plan in RatePlan.objects.filter(room_type__in=room_types, slug='standard'):
            plan_by_room[plan.room_type_id] = plan
        return [{'property': room.property, 'room': room, 'plan': plan_by_room[room.id]} for room in room_types]

    def _bookings(self, rng, hotels, guests, count):
        today = business_today()
        weights = [1 / (rank + 1) ** 0.7 for rank in range(len(guests))]
        for number in range(1, count + 1):
            hotel = rng.choice(hotels)
            guest = rng.choices(guests, weights=weights)[0]
            nights = rng.randint(1, 5)
            check_in = today + timedelta(days=rng.randint(-150, 80))
            status = 'completed' if check_in + timedelta(days=nights) <= today else rng.choice(['confirmed', 'confirmed', 'pending', 'cancelled'])
            nightly = hotel['plan'].base_price
            booking = Booking.objects.create(
                guest=guest, property=hotel['property'], status=status,
                payment_status='paid' if status in ('confirmed', 'completed') else 'pending',
                check_in=check_in, check_out=check_in + timedelta(days=nights), number_of_nights=nights,
                guest_count=2, number_of_rooms=1, total_price=nightly * nights, currency=hotel['property'].currency,
                guest_full_name=guest.full_name, guest_phone=guest.phone_number, guest_email=guest.email,
                special_requests=f'{MARKER} booking {number}',
                expires_at=timezone.now() + timedelta(minutes=15) if status == 'pending' else None,
            )
            BookingItem.objects.create(
                booking=booking, room_type=hotel['room'], rate_plan=hotel['plan'], number_of_rooms=1,
                price_per_night=nightly, currency=hotel['property'].currency)
