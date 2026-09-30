"""
Fill Property.country_ref / region_ref / city_ref from the old text fields.

    python manage.py map_property_geography --dry-run   # report only
    python manage.py map_property_geography             # write

Only properties without a country_ref are touched; unmatched values stay NULL and are
listed with counts. Migration properties/0013 ran this once already.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from geography.mapping import format_report, map_properties
from geography.models import City, Country, Region
from properties.models import Property


class Command(BaseCommand):
    help = 'Map the text location of properties to the Geography dictionary (with a report)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Only print the report')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        with transaction.atomic():
            report = map_properties(Property, Country, Region, City, dry_run=dry_run)
        self.stdout.write(format_report(report, dry_run=dry_run))
