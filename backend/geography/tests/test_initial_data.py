"""
Initial geography data (Geography plan G1): loaded by a data migration, and by
`python manage.py load_geography` (idempotent).
"""
from io import StringIO

import pytest
from django.core.management import call_command

from geography.models import City, Country, Region

UZ_REGIONS_EN = {
    'Andijan Region', 'Bukhara Region', 'Fergana Region', 'Jizzakh Region', 'Khorezm Region',
    'Namangan Region', 'Navoi Region', 'Kashkadarya Region', 'Samarkand Region', 'Sirdarya Region',
    'Surkhandarya Region', 'Tashkent Region', 'Republic of Karakalpakstan', 'Tashkent City',
}


def city(name_en):
    return City.objects.select_related('region__country').get(name_en=name_en)


@pytest.mark.django_db
class TestInitialData:
    """The migration has already loaded the data into the test database."""

    def test_countries(self):
        uz, kz, tr = (Country.objects.get(code=code) for code in ('UZ', 'KZ', 'TR'))
        assert (uz.name_uz, uz.name_ru, uz.name_en, uz.currency) == ("O'zbekiston", 'Узбекистан', 'Uzbekistan', 'UZS')
        assert (kz.name_en, kz.currency) == ('Kazakhstan', 'KZT')
        assert (tr.name_en, tr.currency) == ('Turkey', 'TRY')
        # Uzbekistan first
        assert Country.objects.order_by('sort_order', 'name_en').first() == uz

    def test_uzbekistan_has_its_14_first_level_regions(self):
        regions = Region.objects.filter(country__code='UZ')
        assert set(regions.values_list('name_en', flat=True)) == UZ_REGIONS_EN
        # Every region has at least its regional centre
        for region in regions:
            assert region.cities.exists(), region.name_en

    @pytest.mark.parametrize('en,uz,ru,region_en', [
        ('Tashkent', 'Toshkent', 'Ташкент', 'Tashkent City'),
        ('Samarkand', 'Samarqand', 'Самарканд', 'Samarkand Region'),
        ('Bukhara', 'Buxoro', 'Бухара', 'Bukhara Region'),
        ('Fergana', "Farg'ona", 'Фергана', 'Fergana Region'),
        ('Khiva', 'Xiva', 'Хива', 'Khorezm Region'),
        ('Urgench', 'Urganch', 'Ургенч', 'Khorezm Region'),
        ('Shahrisabz', 'Shahrisabz', 'Шахрисабз', 'Kashkadarya Region'),
        ('Kokand', "Qo'qon", 'Коканд', 'Fergana Region'),
        ('Margilan', "Marg'ilon", 'Маргилан', 'Fergana Region'),
        ('Termez', 'Termiz', 'Термез', 'Surkhandarya Region'),
        ('Nukus', 'Nukus', 'Нукус', 'Republic of Karakalpakstan'),
    ])
    def test_uzbek_cities_in_three_languages(self, en, uz, ru, region_en):
        found = city(en)
        assert (found.name_uz, found.name_ru, found.region.name_en, found.region.country.code) == \
            (uz, ru, region_en, 'UZ')

    def test_karakalpakstan_names(self):
        region = Region.objects.get(name_en='Republic of Karakalpakstan')
        assert (region.name_uz, region.name_ru) == \
            ("Qoraqalpog'iston Respublikasi", 'Республика Каракалпакстан')

    def test_kazakhstan_and_turkey_cover_the_demo_data(self):
        assert city('Almaty').region.country.code == 'KZ'
        assert city('Istanbul').region.country.code == 'TR'
        assert Region.objects.filter(country__code='KZ').count() >= 3
        assert Region.objects.filter(country__code='TR').count() >= 3

    def test_everything_is_active(self):
        assert not Country.objects.filter(is_active=False).exists()
        assert not Region.objects.filter(is_active=False).exists()
        assert not City.objects.filter(is_active=False).exists()

    def test_load_command_is_idempotent_and_keeps_admin_changes(self):
        counts = (Country.objects.count(), Region.objects.count(), City.objects.count())
        khiva = city('Khiva')
        khiva.is_active = False
        khiva.name_en = 'Khiva (Ichan Kala)'
        khiva.save()

        out = StringIO()
        call_command('load_geography', stdout=out)

        assert (Country.objects.count(), Region.objects.count(), City.objects.count()) == counts
        khiva.refresh_from_db()
        assert (khiva.is_active, khiva.name_en) == (False, 'Khiva (Ichan Kala)')
        assert 'Geography' in out.getvalue()
