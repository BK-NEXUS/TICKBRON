"""
Region of a property (Status plan S1).

The region is the existing `Property.state` field ("State/Region" in the partner
wizard). Hotels without one are grouped as "Unspecified" by the Status views.
`backfill_regions_from_city` fills it where the city makes the region obvious.
"""
from decimal import Decimal

import pytest

from properties.models import Property, PropertyType
from properties.regions import UNSPECIFIED_REGION, backfill_regions_from_city
from users.models import User


@pytest.fixture
def owner(db):
    return User.objects.create_user(email='owner@example.com', password='OwnerPassword#123')


@pytest.fixture
def make_property(owner):
    hotel_type = PropertyType.objects.create(name='Hotel', slug='hotel')

    def make(city, state=None, country='Uzbekistan'):
        return Property.objects.create(
            owner=owner, property_type=hotel_type, max_guests=2, address_line1='1 Main Street',
            city=city, state=state, country=country, base_price=Decimal('50.00'),
        )
    return make


@pytest.mark.django_db
class TestBackfillRegionsFromCity:

    def test_fills_the_region_of_obvious_cities(self, make_property):
        tashkent = make_property('Tashkent')
        samarkand = make_property(' samarkand ', state='')
        bukhara = make_property('BUKHARA', state='   ')

        assert backfill_regions_from_city(Property) == 3

        for prop, region in ((tashkent, 'Tashkent'), (samarkand, 'Samarkand'), (bukhara, 'Bukhara')):
            prop.refresh_from_db()
            assert prop.state == region

    def test_never_overwrites_an_existing_region(self, make_property):
        prop = make_property('Tashkent', state='Tashkent Region')

        assert backfill_regions_from_city(Property) == 0
        prop.refresh_from_db()
        assert prop.state == 'Tashkent Region'

    def test_leaves_other_cities_unspecified(self, make_property):
        prop = make_property('Khiva')

        assert backfill_regions_from_city(Property) == 0
        prop.refresh_from_db()
        assert prop.state is None

    def test_unspecified_label(self):
        assert UNSPECIFIED_REGION == 'Unspecified'
