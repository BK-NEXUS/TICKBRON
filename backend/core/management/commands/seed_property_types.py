"""
Standart mehmanxana túrlerin qosıw (hotel, hostel, guest house, apartment, resort).

Jańa server olarsız baslanadı, hám iyeniń "mehmanxana qosıw" formasına biri kerek. Qayta isletiw qáwipsiz: bar
túr (birdey slug) ózgerissiz qaladı.

Paydalanıw: python manage.py seed_property_types
"""
from django.core.management.base import BaseCommand

from properties.models import PropertyType

STANDARD_TYPES = [
    ('Hotel', 'hotel', 'Hotels and guesthouses'),
    ('Hostel', 'hostel', 'Hostels with shared and private rooms'),
    ('Guest house', 'guest-house', 'Small family-run guest houses'),
    ('Apartment', 'apartment', 'Apartments and flats'),
    ('Resort', 'resort', 'Resorts and sanatoriums'),
]


class Command(BaseCommand):
    help = 'Add the standard property types (safe to run again)'

    def handle(self, *args, **options):
        added = 0
        for name, slug, description in STANDARD_TYPES:
            _, created = PropertyType.objects.get_or_create(
                slug=slug, defaults={'name': name, 'description': description})
            added += created
        self.stdout.write(self.style.SUCCESS(f'Property types: {added} added, {len(STANDARD_TYPES) - added} already there'))
