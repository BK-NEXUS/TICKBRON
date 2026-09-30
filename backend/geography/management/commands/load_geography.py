"""
Load the initial Country > Region > City data (geography/data.py).

    python manage.py load_geography

Idempotent: only missing rows are created; existing rows (and admin edits) are kept.
The same data is loaded by migration geography/0002, so this is only needed to
re-add rows that were deleted.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from geography.data import load_geography
from geography.models import City, Country, Region


class Command(BaseCommand):
    help = 'Load the initial Geography data (countries, regions, cities); idempotent'

    def handle(self, *args, **options):
        with transaction.atomic():
            countries, regions, cities = load_geography(Country, Region, City)
        self.stdout.write(self.style.SUCCESS(
            f'Geography loaded: {countries} countries, {regions} regions, {cities} cities created '
            f'({Country.objects.count()} / {Region.objects.count()} / {City.objects.count()} in total).'
        ))
