"""
Demo data for local development: users, three active properties with rooms,
rate plans and 90 days of availability.

    python manage.py seed_demo

Safe to run repeatedly (everything is matched by email/slug/date and updated
in place; booked room counts are kept). Refuses to run when DEBUG is off,
because the demo accounts have well-known passwords.
"""
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from geography.mapping import map_properties
from geography.models import City, Country, Region
from permissions.models import Role
from properties.models import (
    DateInventory, Property, PropertyTranslation, PropertyType, RatePlan, RoomType,
)
from users.models import User

INVENTORY_DAYS = 90

DEMO_USERS = [
    {
        'key': 'admin', 'email': 'admin@tickbron.demo', 'password': 'DemoAdmin#2026',
        'full_name': 'Demo Super Admin', 'phone_number': '+998900000001', 'label': 'Super-admin',
    },
    {
        'key': 'owner', 'email': 'owner@tickbron.demo', 'password': 'DemoOwner#2026',
        'full_name': 'Demo Hotel Owner', 'phone_number': '+998900000002', 'label': 'Hotel owner',
    },
    {
        'key': 'guest', 'email': 'guest@tickbron.demo', 'password': 'DemoGuest#2026',
        'full_name': 'Demo Guest', 'phone_number': '+998900000003', 'label': 'Guest',
    },
]

# Each property: (slug suffix, room types); each room type: (name, occupancy, max, rooms, price, bed)
DEMO_PROPERTIES = [
    {
        'city': 'Tashkent', 'state': 'Tashkent', 'address': '15 Amir Temur Avenue',
        'latitude': Decimal('41.311081'), 'longitude': Decimal('69.279737'),
        'name': 'TICKBRON Demo Hotel Tashkent',
        'description': 'Modern city hotel near Amir Temur Square, a short walk from the metro.',
        'rooms': [
            ('Standard Double', 2, 2, 8, Decimal('60.00'), '1 Queen Bed'),
            ('Deluxe King', 2, 3, 4, Decimal('95.00'), '1 King Bed'),
        ],
    },
    {
        'city': 'Samarkand', 'state': 'Samarkand', 'address': '7 Registan Street',
        'latitude': Decimal('39.654823'), 'longitude': Decimal('66.975670'),
        'name': 'TICKBRON Demo Registan Inn',
        'description': 'Boutique inn with courtyard views, five minutes from the Registan.',
        'rooms': [
            ('Courtyard Twin', 2, 2, 6, Decimal('55.00'), '2 Single Beds'),
            ('Family Suite', 4, 5, 2, Decimal('120.00'), '1 King Bed and 2 Single Beds'),
        ],
    },
    {
        'city': 'Bukhara', 'state': 'Bukhara', 'address': '3 Lyabi-Hauz Lane',
        'latitude': Decimal('39.767966'), 'longitude': Decimal('64.421728'),
        'name': 'TICKBRON Demo Old Town Guesthouse',
        'description': 'Family-run guesthouse in the old town, next to Lyabi-Hauz.',
        'rooms': [
            ('Classic Double', 2, 2, 5, Decimal('45.00'), '1 Double Bed'),
        ],
    },
]


class Command(BaseCommand):
    help = 'Create demo users and three active properties with 90 days of availability (DEBUG only)'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('seed_demo creates accounts with known passwords; it only runs with DEBUG=True.')

        with transaction.atomic():
            users = self._seed_users()
            properties = self._seed_properties(owner=users['owner'], approver=users['admin'])
            # Geography refs from the text location (only these demo properties)
            map_properties(Property, Country, Region, City,
                           queryset=Property.objects.filter(pk__in=[prop.pk for prop, _ in properties]))

        self._print_summary(properties)

    def _seed_users(self):
        owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner',
            defaults={'description': 'Hotel owner role for property management', 'is_system_role': True},
        )
        users = {}
        for spec in DEMO_USERS:
            flags = {
                'admin': {'is_staff': True, 'is_superuser': True, 'role': None},
                'owner': {'is_staff': False, 'is_superuser': False, 'role': owner_role},
                'guest': {'is_staff': False, 'is_superuser': False, 'role': None},
            }[spec['key']]
            user, _ = User.objects.update_or_create(
                email=spec['email'],
                defaults={
                    'full_name': spec['full_name'],
                    'phone_number': spec['phone_number'],
                    'is_active': True,
                    'email_verified': True,
                    'phone_verified': True,
                    **flags,
                },
            )
            user.set_password(spec['password'])
            user.save()
            users[spec['key']] = user
        return users

    def _seed_properties(self, owner, approver):
        hotel_type, _ = PropertyType.objects.get_or_create(
            slug='hotel', defaults={'name': 'Hotel', 'description': 'Hotels and guesthouses'},
        )
        today = timezone.localdate()
        properties = []
        for spec in DEMO_PROPERTIES:
            min_price = min(room[4] for room in spec['rooms'])
            prop, _ = Property.objects.update_or_create(
                owner=owner,
                city=spec['city'],
                address_line1=spec['address'],
                defaults={
                    'property_type': hotel_type,
                    'status': 'active',
                    'is_active': True,
                    'max_guests': max(room[2] for room in spec['rooms']),
                    'bedrooms': len(spec['rooms']),
                    'bathrooms': len(spec['rooms']),
                    'state': spec['state'],
                    'country': 'Uzbekistan',
                    'latitude': spec['latitude'],
                    'longitude': spec['longitude'],
                    'base_price': min_price,
                    'currency': 'USD',
                    'has_wifi': True,
                    'has_ac': True,
                    'approved_at': timezone.now(),
                    'approved_by': approver,
                },
            )
            PropertyTranslation.objects.update_or_create(
                property=prop,
                language='en',
                defaults={
                    'name': spec['name'],
                    'description': spec['description'],
                    'address_line1': spec['address'],
                    'city': spec['city'],
                },
            )
            for name, occupancy, max_occupancy, total_rooms, price, bed in spec['rooms']:
                self._seed_room(prop, name, occupancy, max_occupancy, total_rooms, price, bed, today)
            properties.append((prop, spec['name']))
        return properties

    def _seed_room(self, prop, name, occupancy, max_occupancy, total_rooms, price, bed, today):
        slug = name.lower().replace(' ', '-')
        room, _ = RoomType.objects.update_or_create(
            property=prop,
            slug=slug,
            defaults={
                'name': name,
                'description': f'{name} at {prop.city}',
                'base_occupancy': occupancy,
                'max_occupancy': max_occupancy,
                'base_price': price,
                'currency': 'USD',
                'total_rooms': total_rooms,
                'bed_configuration': bed,
            },
        )
        rate_plans = [
            ('standard', 'Standard Rate', price, 'Free cancellation up to 48 hours before check-in.'),
            ('non_refundable', 'Non-refundable Rate', (price * Decimal('0.9')).quantize(Decimal('0.01')),
             'No refund after booking.'),
        ]
        for rate_type, rate_name, rate_price, policy in rate_plans:
            rate_plan, _ = RatePlan.objects.update_or_create(
                room_type=room,
                slug=rate_type.replace('_', '-'),
                defaults={
                    'name': rate_name,
                    'rate_type': rate_type,
                    'base_price': rate_price,
                    'currency': 'USD',
                    'min_nights': 1,
                    'max_nights': 30,
                    'is_active': True,
                    'cancellation_policy': policy,
                },
            )
            for offset in range(INVENTORY_DAYS):
                date = today + timedelta(days=offset)
                # Weekend nights cost 15% more, so the calendar shows real price differences
                nightly = rate_price * Decimal('1.15') if date.weekday() >= 4 else rate_price
                inventory, created = DateInventory.objects.get_or_create(
                    rate_plan=rate_plan,
                    date=date,
                    defaults={'available_rooms': total_rooms, 'booked_rooms': 0},
                )
                # Refresh availability and price but never touch booked_rooms (real bookings)
                inventory.available_rooms = max(total_rooms, inventory.booked_rooms)
                inventory.price = nightly.quantize(Decimal('0.01'))
                inventory.currency = 'USD'
                inventory.is_available = True
                inventory.save(update_fields=['available_rooms', 'price', 'currency', 'is_available'])

    def _print_summary(self, properties):
        self.stdout.write(self.style.SUCCESS('Demo data ready.'))
        self.stdout.write('')
        self.stdout.write('Properties:')
        for prop, name in properties:
            rooms = prop.room_types.filter(is_deleted=False).count()
            self.stdout.write(f'  #{prop.id} {name} ({prop.city}), {rooms} room types, {INVENTORY_DAYS} days')
        self.stdout.write('')
        self.stdout.write('Demo logins (local development only):')
        for spec in DEMO_USERS:
            self.stdout.write(
                f"  {spec['label']:<12} {spec['email']:<22} password: {spec['password']:<16} "
                f"phone: {spec['phone_number']}"
            )
