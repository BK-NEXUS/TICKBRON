"""
Migration geography/0003 gives the Uzbek regions plain English names (2026-10-02):
"Samarkand Region" -> "Samarkand", "Tashkent City" -> "Tashkent". Only the English names change.

The migration functions are called directly on the test database (a fresh database already has the
new names, so each test first puts the old names back, as an existing database has them).
"""
import importlib

import pytest
from django.apps import apps

from geography.data import GEOGRAPHY, RENAMED_UZ_REGIONS, load_geography
from geography.models import City, Country, Region
from properties.models import Property, PropertyType
from users.models import User

migration = importlib.import_module('geography.migrations.0003_rename_uzbek_regions')


def region(name_en):
    return Region.objects.get(country__code='UZ', name_en=name_en)


@pytest.fixture
def old_names(db):
    """The database as it was before the migration: the 11 renamed regions hold their old names."""
    for old, new in migration.RENAMES:
        Region.objects.filter(country__code='UZ', name_en=new).update(name_en=old)


@pytest.mark.django_db
class TestRename:

    def test_the_migration_list_matches_the_data(self):
        assert {new: old for old, new in migration.RENAMES} == RENAMED_UZ_REGIONS
        uz = next(spec for spec in GEOGRAPHY if spec['code'] == 'UZ')
        english = {names[2] for names, _ in uz['regions']}
        assert english >= set(RENAMED_UZ_REGIONS)
        assert {'Tashkent', 'Tashkent Region'} <= english

    def test_forward_renames_only_the_english_names(self, old_names):
        before = {r.slug: (r.name_uz, r.name_ru) for r in Region.objects.filter(country__code='UZ')}
        migration.forward(apps, None)
        for old, new in migration.RENAMES:
            assert not Region.objects.filter(country__code='UZ', name_en=old).exists(), old
            assert Region.objects.filter(country__code='UZ', name_en=new).exists(), new
        # uz and ru names (the official forms) and the slugs are untouched
        after = {r.slug: (r.name_uz, r.name_ru) for r in Region.objects.filter(country__code='UZ')}
        assert after == before
        assert region('Tashkent').slug == 'uz-tashkent-city'
        assert region('Samarkand').slug == 'uz-samarkand-region'

    def test_tashkent_and_tashkent_region_stay_two_regions(self, old_names):
        migration.forward(apps, None)
        city, oblast = region('Tashkent'), region('Tashkent Region')
        assert city.id != oblast.id
        assert (city.name_uz, oblast.name_uz) == ('Toshkent shahri', 'Toshkent viloyati')
        assert (city.name_ru, oblast.name_ru) == ('город Ташкент', 'Ташкентская область')

    def test_regions_that_were_not_renamed_keep_their_names(self, old_names):
        migration.forward(apps, None)
        assert Region.objects.filter(country__code='UZ', name_en='Republic of Karakalpakstan').exists()
        assert Region.objects.filter(name_en='Almaty City').exists()
        assert Region.objects.filter(name_en='Istanbul Province').exists()

    def test_the_text_state_of_properties_follows(self, old_names):
        owner = User.objects.create_user(email='owner@example.com', password='x')
        hotel = PropertyType.objects.create(name='Hotel', slug='hotel')
        samarkand = region('Samarkand Region')
        city = City.objects.get(region=samarkand, name_en='Samarkand')
        prop = Property.objects.create(
            owner=owner, property_type=hotel, max_guests=2, address_line1='1 Main St', base_price=50,
            country_ref=samarkand.country, region_ref=samarkand, city_ref=city)
        Property.objects.filter(pk=prop.pk).update(state='Samarkand Region')
        other = Property.objects.create(
            owner=owner, property_type=hotel, max_guests=2, address_line1='2 Main St', base_price=50,
            country_ref=samarkand.country, region_ref=samarkand, city_ref=city)
        Property.objects.filter(pk=other.pk).update(state='My own text')

        migration.forward(apps, None)

        prop.refresh_from_db()
        other.refresh_from_db()
        assert prop.state == 'Samarkand'
        assert other.state == 'My own text'  # only the copies of the old name change

    def test_a_name_edited_by_an_admin_is_left_alone(self, old_names):
        Region.objects.filter(name_en='Bukhara Region').update(name_en='Bukhara Oasis')
        migration.forward(apps, None)
        assert Region.objects.filter(country__code='UZ', name_en='Bukhara Oasis').exists()
        assert not Region.objects.filter(country__code='UZ', name_en='Bukhara').exists()

    def test_a_rename_that_would_clash_is_skipped(self, old_names):
        uz = Country.objects.get(code='UZ')
        Region.objects.create(country=uz, name_uz='Boshqa', name_ru='Другая', name_en='Khorezm', slug='uz-other')
        migration.forward(apps, None)
        assert region('Khorezm Region').slug == 'uz-khorezm-region'  # kept its old name, no IntegrityError

    def test_running_forward_twice_changes_nothing_more(self, old_names):
        migration.forward(apps, None)
        names = sorted(Region.objects.values_list('name_en', flat=True))
        migration.forward(apps, None)
        assert sorted(Region.objects.values_list('name_en', flat=True)) == names

    def test_reverse_restores_the_old_names_and_the_text(self, old_names):
        migration.forward(apps, None)
        migration.backward(apps, None)
        for old, new in migration.RENAMES:
            assert Region.objects.filter(country__code='UZ', name_en=old).exists(), old
            assert not Region.objects.filter(country__code='UZ', name_en=new).exists(), new
        assert region('Tashkent Region')  # never renamed


@pytest.mark.django_db
class TestLoadGeographyKeepsFindingRenamedRows:

    def test_load_geography_after_the_rename_creates_no_duplicates(self, old_names):
        migration.forward(apps, None)
        before = (Country.objects.count(), Region.objects.count(), City.objects.count())
        created = load_geography(Country, Region, City)
        assert created == (0, 0, 0)
        assert (Country.objects.count(), Region.objects.count(), City.objects.count()) == before

    def test_a_fresh_install_gets_the_new_names_and_the_old_slugs(self, db):
        assert region('Samarkand').slug == 'uz-samarkand-region'
        assert region('Tashkent').slug == 'uz-tashkent-city'
        assert region('Tashkent Region').slug == 'uz-tashkent-region'
