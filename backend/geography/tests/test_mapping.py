"""
Mapping the old text location of properties to the Geography dictionary (Geography plan G2; the city level was
removed 2026-11-10, so only country and region are mapped from the text: the town stays text).
Uses the initial data loaded by migration geography/0002.
"""
from decimal import Decimal

import pytest

from geography.mapping import GeographyIndex, format_report, map_properties, normalize
from geography.models import Country, Region
from properties.models import Property, PropertyType
from users.models import User


@pytest.fixture
def make(db):
    owner = User.objects.create_user(email='owner@example.com', password='OwnerPassword#123')
    hotel_type = PropertyType.objects.create(name='Hotel', slug='hotel')

    def _make(country, city, state=None):
        return Property.objects.create(
            owner=owner, property_type=hotel_type, max_guests=2, address_line1='1 Main Street',
            city=city, state=state, country=country, base_price=Decimal('50.00'),
        )
    return _make


def run(dry_run=False):
    return map_properties(Property, Country, Region, dry_run=dry_run)


def refs(prop):
    prop.refresh_from_db()
    return (
        prop.country_ref.code if prop.country_ref else None,
        prop.region_ref.name_en if prop.region_ref else None,
    )


def test_normalize():
    assert normalize("  O‘zbekiston ") == 'ozbekiston'
    assert normalize("Farg'ona  viloyati") == 'fargona viloyati'
    assert normalize(None) == ''


@pytest.mark.django_db
class TestMapProperties:

    @pytest.mark.parametrize('country,state,expected', [
        ('Uzbekistan', 'Tashkent', ('UZ', 'Tashkent')),
        (' uzbekistan ', 'Samarkand', ('UZ', 'Samarkand')),
        ("O'zbekiston", 'Buxoro viloyati', ('UZ', 'Bukhara')),
        ('Узбекистан', 'Ферганская область', ('UZ', 'Fergana')),
        ('UZ', None, ('UZ', None)),
        ('Kazakhstan', 'Almaty', ('KZ', 'Almaty City')),
        ('Türkiye', None, ('TR', None)),
        ('Turkey', 'Istanbul', ('TR', 'Istanbul Province')),
    ])
    def test_matches_names_aliases_and_languages(self, make, country, state, expected):
        prop = make(country, 'Somewhere', state)
        run()
        assert refs(prop) == expected

    def test_the_typed_town_is_never_touched(self, make):
        prop = make('Uzbekistan', 'My Own Town', state='Samarkand')
        run()
        prop.refresh_from_db()
        assert prop.city == 'My Own Town'

    def test_unknown_values_stay_null_and_are_reported(self, make):
        make('Atlantis', 'Poseidonia')
        make('Atlantis', 'Poseidonia')
        unknown_region = make('Uzbekistan', 'Somewhere', state='Nowhere')
        report = run()

        assert refs(unknown_region) == ('UZ', None)
        assert report['properties'] == 3
        assert (report['country'], report['region']) == (1, 0)
        assert report['unmatched_country'] == {'Atlantis': 2}
        assert report['unmatched_region'] == {'Uzbekistan / Nowhere': 1}
        assert 'city' not in report['unmatched_region']
        text = format_report(report)
        assert 'Atlantis' in text and 'left NULL' in text and 'city' not in text

    def test_a_region_of_another_country_is_not_used(self, make):
        prop = make('Kazakhstan', 'Somewhere', state='Samarkand')
        run()
        assert refs(prop) == ('KZ', None)

    def test_dry_run_writes_nothing(self, make):
        prop = make('Uzbekistan', 'Somewhere', state='Tashkent')
        report = run(dry_run=True)
        assert report['region'] == 1
        assert refs(prop) == (None, None)
        assert 'dry run' in format_report(report, dry_run=True)

    def test_existing_refs_are_kept_and_a_second_run_changes_nothing(self, make):
        prop = make('Uzbekistan', 'Somewhere', state='Tashkent')
        khorezm = Region.objects.get(country__code='UZ', name_en='Khorezm')
        prop.country_ref, prop.region_ref = khorezm.country, khorezm
        prop.save()
        run()
        assert refs(prop) == ('UZ', 'Khorezm')
        assert run()['already_mapped'] == 1


@pytest.mark.django_db
class TestOldRegionTexts:
    """
    The English region names lost their "Region" / "City" words (migration geography/0003), but the
    old text values must still map to the right regions. "Tashkent" (the city) and "Tashkent Region"
    are two regions.
    """

    @pytest.mark.parametrize('state,expected', [
        ('Tashkent', 'Tashkent'),
        ('Tashkent City', 'Tashkent'),
        ('tashkent city', 'Tashkent'),
        ('Toshkent shahri', 'Tashkent'),
        ('Toshkent shahar', 'Tashkent'),
        ('город Ташкент', 'Tashkent'),
        ('Tashkent Region', 'Tashkent Region'),
        ('tashkent region', 'Tashkent Region'),
        ('Toshkent viloyati', 'Tashkent Region'),
        ('Ташкентская область', 'Tashkent Region'),
        ('Samarkand', 'Samarkand'),
        ('Samarkand Region', 'Samarkand'),
        ('Samarqand viloyati', 'Samarkand'),
        ('Самаркандская область', 'Samarkand'),
        ('Bukhara Region', 'Bukhara'),
        ('Buxoro viloyati', 'Bukhara'),
        ('Khorezm Region', 'Khorezm'),
        ('Хорезмская область', 'Khorezm'),
        ('Fergana Region', 'Fergana'),
        ('Republic of Karakalpakstan', 'Republic of Karakalpakstan'),
    ])
    def test_region_text(self, state, expected):
        country, region, city = GeographyIndex(Country, Region).match('Uzbekistan', state, None)
        assert (country.code, region.name_en, city) == ('UZ', expected, None)

    def test_tashkent_and_tashkent_region_are_two_regions(self):
        regions = Region.objects.filter(country__code='UZ', name_en__in=['Tashkent', 'Tashkent Region'])
        assert regions.count() == 2

    def test_the_town_text_no_longer_decides_the_region(self):
        # With the city dictionary gone, a state that does not fit the town is not "corrected" by the town
        _, region, city = GeographyIndex(Country, Region).match('Uzbekistan', 'Tashkent', 'Chirchiq')
        assert (region.name_en, city) == ('Tashkent', None)
