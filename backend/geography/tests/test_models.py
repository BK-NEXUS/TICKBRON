"""
Geography dictionary: Country > Region (Geography plan G1; the city level was removed 2026-11-10).
"""
import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from geography.models import Country, Region


@pytest.fixture
def world(db):
    country = Country.objects.create(code='XA', name_uz='Xland', name_ru='Иксландия', name_en='Xland',
                                     currency='USD')
    region = Region.objects.create(country=country, name_uz='Sharq', name_ru='Восток', name_en='East')
    return country, region


@pytest.mark.django_db
class TestModels:

    def test_names_in_three_languages(self, world):
        country, region = world
        assert (region.name('uz'), region.name('ru'), region.name('en')) == ('Sharq', 'Восток', 'East')
        # Unknown language or missing name: English
        assert region.name('de') == 'East'
        assert str(region) == 'East' and str(country) == 'Xland'

    def test_active_by_default_and_sort_order(self, world):
        country, region = world
        assert country.is_active and region.is_active
        assert (country.sort_order, region.sort_order) == (0, 0)

    def test_code_is_upper_case_and_unique(self, world):
        other = Country.objects.create(code='xb', name_uz='B', name_ru='Б', name_en='B', currency='usd')
        assert (other.code, other.currency) == ('XB', 'USD')
        with pytest.raises(IntegrityError), transaction.atomic():
            Country.objects.create(code='XA', name_uz='Dup', name_ru='Дуп', name_en='Dup', currency='USD')

    def test_region_names_are_unique_inside_the_country(self, world):
        country, _ = world
        with pytest.raises(IntegrityError), transaction.atomic():
            Region.objects.create(country=country, name_uz='S', name_ru='В', name_en='East')

    def test_the_same_name_is_allowed_under_another_country(self, world):
        other = Country.objects.create(code='XB', name_uz='B', name_ru='Б', name_en='B', currency='USD')
        Region.objects.create(country=other, name_uz='S', name_ru='В', name_en='East')

    def test_in_use_rows_cannot_be_deleted(self, world):
        country, region = world
        with pytest.raises(ProtectedError):
            country.delete()
        # A leaf can be deleted; hiding is done with is_active=False
        region.delete()

    def test_stable_slug_is_set_once(self, world):
        _, region = world
        assert region.slug == 'xa-east'
        region.name_en = 'Renamed'
        region.save()
        region.refresh_from_db()
        # Renaming does not change the key the initial data is matched by
        assert region.slug == 'xa-east'
