"""
Add the standard property types (hotel, hostel, guest house, apartment, resort).

A new server starts with none, and the owner's "add a hotel" form needs one. Safe to run again: a type
that already exists (same slug) is left as it is.

Usage: python manage.py seed_property_types
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
