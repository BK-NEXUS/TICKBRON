"""
Property.country_ref / region_ref / city_ref di eski tekst maydanlardan toltırıw.

    python manage.py map_property_geography --dry-run   # tek esabat
    python manage.py map_property_geography             # jazıw

Tek country_ref i joq mehmanxanalarǵa tiyiledi; sáykes kelmegen mánisler NULL qaladı hám
sanları menen dizimlenedi. properties/0013 migration bunı aldınan bir ret isledi.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from geography.mapping import format_report, map_properties
from geography.models import Country, Region
from properties.models import Property


class Command(BaseCommand):
    help = 'Map the text location of properties to the Geography dictionary (with a report)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Only print the report')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        with transaction.atomic():
            report = map_properties(Property, Country, Region, dry_run=dry_run)
        self.stdout.write(format_report(report, dry_run=dry_run))
