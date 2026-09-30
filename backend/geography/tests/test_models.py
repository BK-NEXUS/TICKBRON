"""
Geography dictionary: Country > Region > City (Geography plan G1).
"""
import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from geography.models import City, Country, Region


@pytest.fixture
def world(db):
    country = Country.objects.create(code='XA', name_uz='Xland', name_ru='Иксландия', name_en='Xland',
                                     currency='USD')
    region = Region.objects.create(country=country, name_uz='Sharq', name_ru='Восток', name_en='East')
    city = City.objects.create(region=region, name_uz='Poytaxt', name_ru='Столица', name_en='Capital')
    return country, region, city


@pytest.mark.django_db
class TestModels:

    def test_names_in_three_languages(self, world):
        country, region, city = world
        assert (city.name('uz'), city.name('ru'), city.name('en')) == ('Poytaxt', 'Столица', 'Capital')
        # Unknown language or missing name: English
        assert city.name('de') == 'Capital'
        assert str(city) == 'Capital' and str(region) == 'East' and str(country) == 'Xland'

    def test_active_by_default_and_sort_order(self, world):
        country, region, city = world
        assert country.is_active and region.is_active and city.is_active
        assert (country.sort_order, region.sort_order, city.sort_order) == (0, 0, 0)

    def test_code_is_upper_case_and_unique(self, world):
        other = Country.objects.create(code='xb', name_uz='B', name_ru='Б', name_en='B', currency='usd')
        assert (other.code, other.currency) == ('XB', 'USD')
        with pytest.raises(IntegrityError), transaction.atomic():
            Country.objects.create(code='XA', name_uz='Dup', name_ru='Дуп', name_en='Dup', currency='USD')

    def test_names_are_unique_inside_the_parent(self, world):
        country, region, _ = world
        with pytest.raises(IntegrityError), transaction.atomic():
            Region.objects.create(country=country, name_uz='S', name_ru='В', name_en='East')
        with pytest.raises(IntegrityError), transaction.atomic():
            City.objects.create(region=region, name_uz='P', name_ru='С', name_en='Capital')

    def test_the_same_name_is_allowed_under_another_parent(self, world):
        country, region, _ = world
        other_region = Region.objects.create(country=country, name_uz='G', name_ru='З', name_en='West')
        City.objects.create(region=other_region, name_uz='P', name_ru='С', name_en='Capital')

    def test_in_use_rows_cannot_be_deleted(self, world):
        country, region, city = world
        with pytest.raises(ProtectedError):
            country.delete()
        with pytest.raises(ProtectedError):
            region.delete()
        # A leaf can be deleted; hiding is done with is_active=False
        city.delete()

    def test_stable_slug_is_set_once(self, world):
        country, region, city = world
        assert (region.slug, city.slug) == ('xa-east', 'xa-east-capital')
        city.name_en = 'Renamed'
        city.save()
        city.refresh_from_db()
        # Renaming does not change the key the initial data is matched by
        assert city.slug == 'xa-east-capital'
