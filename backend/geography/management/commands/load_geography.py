"""
Dáslepki Country > Region maǵlıwmatın júklew (geography/data.py).

    python manage.py load_geography

Idempotent: tek joq qatarlar jaratıladı; bar qatarlar (hám admin ózgerisleri) saqlanadı.
Sol maǵlıwmat geography/0002 migration arqalı da júklenedi, sol sebepli bul tek
óshirilgen qatarlardı qayta qosıw kerek bolǵanda kerek.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from geography.data import load_geography
from geography.models import Country, Region


class Command(BaseCommand):
    help = 'Load the initial Geography data (countries, regions); idempotent'

    def handle(self, *args, **options):
        with transaction.atomic():
            countries, regions, _cities = load_geography(Country, Region)
        self.stdout.write(self.style.SUCCESS(
            f'Geography loaded: {countries} countries, {regions} regions created '
            f'({Country.objects.count()} / {Region.objects.count()} in total).'
        ))
