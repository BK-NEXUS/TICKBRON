"""
Property.country_ref / region_ref (Geography plan G2, city level removed 2026-11-10): the old text fields
country / state are filled from the English names whenever the refs are set, so older code that reads the text
keeps working. The town (city) is plain text and is never touched by the refs.
"""
from decimal import Decimal

import pytest
from django.db.models import ProtectedError

from geography.models import Region
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
        assert (prop.country_ref, prop.region_ref) == (None, None)
        # Without refs the text is left as it is
        prop.save()
        prop.refresh_from_db()
        assert (prop.country, prop.state, prop.city) == ('old country', 'old state', 'old city')

    def test_country_and_state_text_follow_the_refs_and_the_town_is_left_alone(self, prop):
        khorezm = Region.objects.get(country__code='UZ', name_en='Khorezm')
        prop.country_ref, prop.region_ref = khorezm.country, khorezm
        prop.save()
        prop.refresh_from_db()
        assert (prop.country, prop.state, prop.city) == ('Uzbekistan', 'Khorezm', 'old city')

    def test_only_the_refs_that_are_set_are_copied(self, prop):
        khorezm = Region.objects.get(country__code='UZ', name_en='Khorezm')
        prop.country_ref = khorezm.country
        prop.save()
        prop.refresh_from_db()
        assert (prop.country, prop.state, prop.city) == ('Uzbekistan', 'old state', 'old city')

    def test_saving_only_the_ref_fields_also_saves_the_copied_text(self, prop):
        khorezm = Region.objects.get(country__code='UZ', name_en='Khorezm')
        prop.country_ref, prop.region_ref = khorezm.country, khorezm
        prop.save(update_fields=['country_ref', 'region_ref'])
        prop.refresh_from_db()
        assert (prop.country, prop.state) == ('Uzbekistan', 'Khorezm')

    def test_a_region_in_use_cannot_be_deleted(self, prop):
        khorezm = Region.objects.get(country__code='UZ', name_en='Khorezm')
        prop.region_ref = khorezm
        prop.save()
        with pytest.raises(ProtectedError):
            khorezm.delete()
