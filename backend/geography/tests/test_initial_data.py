"""
Dáslepki geografiya maǵlıwmatı (Geography reje G1): data migration arqalı júklenedi, hám
`python manage.py load_geography` arqalı (idempotent). Qala dárejesi 2026-11-10 de alıp taslandı: tek mámleketler hám
regionlar.
"""
from io import StringIO

import pytest
from django.core.management import call_command

from geography.models import Country, Region

UZ_REGIONS_EN = {
    'Andijan', 'Bukhara', 'Fergana', 'Jizzakh', 'Khorezm',
    'Namangan', 'Navoi', 'Kashkadarya', 'Samarkand', 'Sirdarya',
    'Surkhandarya', 'Tashkent Region', 'Republic of Karakalpakstan', 'Tashkent',
}


@pytest.mark.django_db
class TestInitialData:
    """Migration maǵlıwmattı test database ge aldınan júkledi."""

    def test_countries(self):
        uz, kz, tr = (Country.objects.get(code=code) for code in ('UZ', 'KZ', 'TR'))
        assert (uz.name_uz, uz.name_ru, uz.name_en, uz.currency) == ("O'zbekiston", 'Узбекистан', 'Uzbekistan', 'UZS')
        assert (kz.name_en, kz.currency) == ('Kazakhstan', 'KZT')
        assert (tr.name_en, tr.currency) == ('Turkey', 'TRY')
        # Aldın Ózbekstan
        assert Country.objects.order_by('sort_order', 'name_en').first() == uz

    def test_uzbekistan_has_its_14_first_level_regions(self):
        regions = Region.objects.filter(country__code='UZ')
        assert set(regions.values_list('name_en', flat=True)) == UZ_REGIONS_EN

    @pytest.mark.parametrize('en,uz,ru', [
        ('Tashkent', 'Toshkent shahri', 'город Ташкент'),
        ('Samarkand', 'Samarqand viloyati', 'Самаркандская область'),
        ('Bukhara', 'Buxoro viloyati', 'Бухарская область'),
        ('Khorezm', 'Xorazm viloyati', 'Хорезмская область'),
        ('Republic of Karakalpakstan', "Qoraqalpog'iston Respublikasi", 'Республика Каракалпакстан'),
    ])
    def test_uzbek_regions_in_three_languages(self, en, uz, ru):
        region = Region.objects.get(country__code='UZ', name_en=en)
        assert (region.name_uz, region.name_ru) == (uz, ru)

    def test_kazakhstan_and_turkey_have_regions_for_the_demo_data(self):
        assert Region.objects.filter(country__code='KZ').count() >= 3
        assert Region.objects.filter(country__code='TR').count() >= 3

    def test_everything_is_active(self):
        assert not Country.objects.filter(is_active=False).exists()
        assert not Region.objects.filter(is_active=False).exists()

    def test_load_command_is_idempotent_and_keeps_admin_changes(self):
        counts = (Country.objects.count(), Region.objects.count())
        khorezm = Region.objects.get(country__code='UZ', name_en='Khorezm')
        khorezm.is_active = False
        khorezm.name_en = 'Khorezm (Ichan Kala)'
        khorezm.save()

        out = StringIO()
        call_command('load_geography', stdout=out)

        assert (Country.objects.count(), Region.objects.count()) == counts
        khorezm.refresh_from_db()
        assert (khorezm.is_active, khorezm.name_en) == (False, 'Khorezm (Ichan Kala)')
        assert 'Geography' in out.getvalue()
        assert 'cities' not in out.getvalue()
