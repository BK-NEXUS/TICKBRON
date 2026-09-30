"""
Mapping the old text location of properties to the Geography dictionary (Geography plan G2).
Uses the initial data loaded by migration geography/0002.
"""
from decimal import Decimal

import pytest

from geography.mapping import format_report, map_properties, normalize
from geography.models import City, Country, Region
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
    return map_properties(Property, Country, Region, City, dry_run=dry_run)


def refs(prop):
    prop.refresh_from_db()
    return (
        prop.country_ref.code if prop.country_ref else None,
        prop.region_ref.name_en if prop.region_ref else None,
        prop.city_ref.name_en if prop.city_ref else None,
    )


def test_normalize():
    assert normalize("  O‘zbekiston ") == 'ozbekiston'
    assert normalize("Farg'ona  viloyati") == 'fargona viloyati'
    assert normalize(None) == ''


@pytest.mark.django_db
class TestMapProperties:

    @pytest.mark.parametrize('country,state,city,expected', [
        ('Uzbekistan', 'Tashkent', 'Tashkent', ('UZ', 'Tashkent City', 'Tashkent')),
        (' uzbekistan ', None, 'samarkand', ('UZ', 'Samarkand Region', 'Samarkand')),
        ("O'zbekiston", 'Buxoro viloyati', 'Buxoro', ('UZ', 'Bukhara Region', 'Bukhara')),
        ('Ozbekiston', '', 'Xiva', ('UZ', 'Khorezm Region', 'Khiva')),
        ('Узбекистан', 'Ферганская область', 'Коканд', ('UZ', 'Fergana Region', 'Kokand')),
        ('UZ', 'Samarkand', None, ('UZ', 'Samarkand Region', None)),
        ('Kazakhstan', 'Almaty', 'Almaty', ('KZ', 'Almaty City', 'Almaty')),
        ('Türkiye', None, 'Cappadocia', ('TR', 'Nevsehir Province', 'Goreme')),
        ('Turkey', 'Istanbul', 'Istanbul', ('TR', 'Istanbul Province', 'Istanbul')),
    ])
    def test_matches_names_aliases_and_languages(self, make, country, state, city, expected):
        prop = make(country, city or 'Somewhere', state)
        if city is None:
            Property.objects.filter(pk=prop.pk).update(city='')
        run()
        assert refs(prop) == expected

    def test_the_city_decides_the_region(self, make):
        # "Tashkent" as a state is ambiguous (the city or the region); the city settles it
        prop = make('Uzbekistan', 'Chirchiq', state='Tashkent')
        run()
        assert refs(prop) == ('UZ', 'Tashkent Region', 'Chirchiq')

    def test_unknown_values_stay_null_and_are_reported(self, make):
        make('Atlantis', 'Poseidonia')
        make('Atlantis', 'Poseidonia')
        unknown_city = make('Uzbekistan', 'Nowhere', state='Nowhere')
        report = run()

        assert refs(unknown_city) == ('UZ', None, None)
        assert report['properties'] == 3
        assert (report['country'], report['region'], report['city']) == (1, 0, 0)
        assert report['unmatched_country'] == {'Atlantis': 2}
        assert report['unmatched_city'] == {'Uzbekistan / Nowhere': 1}
        text = format_report(report)
        assert 'Atlantis' in text and 'left NULL' in text

    def test_a_city_of_another_country_is_not_used(self, make):
        prop = make('Kazakhstan', 'Samarkand')
        run()
        assert refs(prop) == ('KZ', None, None)

    def test_dry_run_writes_nothing(self, make):
        prop = make('Uzbekistan', 'Tashkent')
        report = run(dry_run=True)
        assert report['city'] == 1
        assert refs(prop) == (None, None, None)
        assert 'dry run' in format_report(report, dry_run=True)

    def test_existing_refs_are_kept_and_a_second_run_changes_nothing(self, make):
        prop = make('Uzbekistan', 'Tashkent')
        khiva = City.objects.get(name_en='Khiva')
        prop.country_ref, prop.region_ref, prop.city_ref = khiva.region.country, khiva.region, khiva
        prop.save()
        run()
        assert refs(prop) == ('UZ', 'Khorezm Region', 'Khiva')
        assert run()['already_mapped'] == 1
