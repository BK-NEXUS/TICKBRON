"""
Search and suggestions match location names in all three languages through the
Geography refs, and still fall back to the old text fields for unmapped rows
(Geography plan G4).

"Toshkent", "Ташкент" and "Tashkent" must find the same hotel.
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from geography.models import City
from properties.models import Property, PropertyType
from users.models import User

SEARCH = '/api/v1/properties/search/'
SUGGEST = '/api/v1/properties/search/suggestions/'


@pytest.fixture
def owner(db):
    return User.objects.create_user(email='owner@example.com', password='x')


@pytest.fixture
def hotel_type(db):
    return PropertyType.objects.create(name='Hotel', slug='hotel')


def make(owner, hotel_type, n, city=None, **extra):
    """A public hotel in a dictionary city (by English name), or with text-only location."""
    fields = dict(status='active', max_guests=2, address_line1=f'{n} Main St', base_price=Decimal('60.00'))
    if city:
        row = City.objects.select_related('region__country').get(region__country__code='UZ', name_en=city)
        fields.update(country_ref=row.region.country, region_ref=row.region, city_ref=row)
    fields.update(extra)
    return Property.objects.create(owner=owner, property_type=hotel_type, **fields)


def legacy(owner, hotel_type, n, city, country):
    """A public hotel that was never mapped to the dictionary: text location only."""
    return Property.objects.create(
        owner=owner, property_type=hotel_type, status='active', max_guests=2, address_line1=f'{n} Old St',
        base_price=Decimal('40.00'), city=city, country=country)


def ids(response):
    return [row['id'] for row in response.data['results']]


@pytest.mark.django_db
class TestSearchAcrossLanguages:

    @pytest.mark.parametrize('term', ['Tashkent', 'Toshkent', 'Ташкент', 'ташкент', 'toshk'])
    @pytest.mark.parametrize('param', ['location', 'q'])
    def test_every_spelling_finds_the_same_hotel(self, owner, hotel_type, term, param):
        tashkent = make(owner, hotel_type, 1, city='Tashkent')
        samarkand = make(owner, hotel_type, 2, city='Samarkand')
        found = ids(APIClient().get(SEARCH, {param: term}))
        assert tashkent.id in found
        assert samarkand.id not in found

    @pytest.mark.parametrize('term', ['Uzbekistan', "O'zbekiston", 'Узбекистан'])
    def test_country_names_in_every_language(self, owner, hotel_type, term):
        uz = make(owner, hotel_type, 1, city='Khiva')
        elsewhere = legacy(owner, hotel_type, 2, city='Atlantis', country='Elsewhere')
        found = ids(APIClient().get(SEARCH, {'location': term}))
        assert uz.id in found and elsewhere.id not in found

    @pytest.mark.parametrize('term', ['Khorezm', 'Xorazm', 'Хорезм'])
    def test_region_names_in_every_language(self, owner, hotel_type, term):
        khiva = make(owner, hotel_type, 1, city='Khiva')
        samarkand = make(owner, hotel_type, 2, city='Samarkand')
        found = ids(APIClient().get(SEARCH, {'location': term}))
        assert khiva.id in found and samarkand.id not in found

    def test_unmapped_hotels_are_still_found_by_their_text_fields(self, owner, hotel_type):
        old = legacy(owner, hotel_type, 1, city='Atlantis', country='Elsewhere')
        assert old.id in ids(APIClient().get(SEARCH, {'location': 'Atlantis'}))
        assert old.id in ids(APIClient().get(SEARCH, {'q': 'atlantis'}))

    def test_a_hidden_dictionary_row_does_not_stop_search(self, owner, hotel_type):
        tashkent = make(owner, hotel_type, 1, city='Tashkent')
        City.objects.filter(pk=tashkent.city_ref_id).update(is_active=False)
        assert tashkent.id in ids(APIClient().get(SEARCH, {'location': 'Ташкент'}))

    def test_no_duplicate_rows_when_several_names_match(self, owner, hotel_type):
        tashkent = make(owner, hotel_type, 1, city='Tashkent')
        # "Tash" matches the city, its region (Tashkent city) and the text fields at once
        assert ids(APIClient().get(SEARCH, {'location': 'Tash'})).count(tashkent.id) == 1
        assert ids(APIClient().get(SEARCH, {'q': 'Tash'})).count(tashkent.id) == 1


@pytest.mark.django_db
class TestSuggestions:

    def get(self, q):
        response = APIClient().get(SUGGEST, {'q': q, 'limit': 20})
        assert response.status_code == 200
        return response.data['suggestions']

    def test_suggests_the_name_in_the_language_the_user_typed(self, owner, hotel_type):
        make(owner, hotel_type, 1, city='Tashkent')
        assert 'Ташкент' in self.get('Таш')
        assert 'Toshkent' in self.get('Tosh')
        assert 'Tashkent' in self.get('Tash')

    def test_every_suggestion_finds_the_hotel_when_searched(self, owner, hotel_type):
        hotel = make(owner, hotel_type, 1, city='Tashkent')
        for typed in ('Таш', 'Tosh', 'Tash'):
            suggestions = self.get(typed)
            assert suggestions, typed
            for suggestion in suggestions:
                assert hotel.id in ids(APIClient().get(SEARCH, {'location': suggestion})), suggestion

    def test_only_places_with_public_hotels_are_suggested(self, owner, hotel_type):
        make(owner, hotel_type, 1, city='Tashkent', status='draft')
        make(owner, hotel_type, 2, city='Samarkand', is_active=False)
        assert self.get('Ташкент') == []
        assert self.get('Samar') == []

    def test_unmapped_text_is_still_suggested(self, owner, hotel_type):
        legacy(owner, hotel_type, 1, city='Atlantis', country='Elsewhere')
        assert 'Atlantis' in self.get('Atlan')

    def test_no_duplicates_and_the_limit_holds(self, owner, hotel_type):
        make(owner, hotel_type, 1, city='Tashkent')
        make(owner, hotel_type, 2, city='Tashkent')
        suggestions = self.get('Tashkent')
        assert len(suggestions) == len(set(suggestions))
        response = APIClient().get(SUGGEST, {'q': 'a', 'limit': 3})
        assert response.data['suggestions'] == []  # still needs two characters
        assert len(APIClient().get(SUGGEST, {'q': 'Ta', 'limit': 1}).data['suggestions']) <= 1
