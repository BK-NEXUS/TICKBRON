"""
Property.country_ref / region_ref / city_ref (Geography plan G2): the old text fields
country / state / city are filled from the English names whenever the refs are set,
so older code that reads the text keeps working.
"""
from decimal import Decimal

import pytest
from django.db.models import ProtectedError

from geography.models import City
from properties.models import Property, PropertyType
from users.models import User


@pytest.fixture
def prop(db):
    owner = User.objects.create_user(email='owner@example.com', password='OwnerPassword#123')
    hotel_type = PropertyType.objects.create(name='Hotel', slug='hotel')
    return Property.objects.create(
        owner=owner, property_type=hotel_type, max_guests=2, address_line1='1 Main Street',
        city='old city', state='old state', country='old country', base_price=Decimal('50.00'),
    )


@pytest.mark.django_db
class TestPropertyGeographyRefs:

    def test_refs_are_optional(self, prop):
        assert (prop.country_ref, prop.region_ref, prop.city_ref) == (None, None, None)
        # Without refs the text is left as it is
        prop.save()
        prop.refresh_from_db()
        assert (prop.country, prop.state, prop.city) == ('old country', 'old state', 'old city')

    def test_text_fields_follow_the_refs(self, prop):
        khiva = City.objects.get(name_en='Khiva')
        prop.country_ref, prop.region_ref, prop.city_ref = khiva.region.country, khiva.region, khiva
        prop.save()
        prop.refresh_from_db()
        assert (prop.country, prop.state, prop.city) == ('Uzbekistan', 'Khorezm Region', 'Khiva')

    def test_only_the_refs_that_are_set_are_copied(self, prop):
        khiva = City.objects.get(name_en='Khiva')
        prop.country_ref = khiva.region.country
        prop.save()
        prop.refresh_from_db()
        assert (prop.country, prop.state, prop.city) == ('Uzbekistan', 'old state', 'old city')

    def test_a_city_in_use_cannot_be_deleted(self, prop):
        khiva = City.objects.get(name_en='Khiva')
        prop.city_ref = khiva
        prop.save()
        with pytest.raises(ProtectedError):
            khiva.delete()
