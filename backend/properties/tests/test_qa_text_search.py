"""QA: a multi-word search must match properties that contain every word, not any one of them."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from properties.models import Property, PropertyType
from properties.search import PropertySearchService

User = get_user_model()


class MultiWordSearchTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user(email='owner@example.com', password='testpass123')
        kind = PropertyType.objects.create(name='Hotel', slug='hotel')

        def make(address, city):
            return Property.objects.create(
                owner=owner, property_type=kind, status='active', max_guests=2, bedrooms=1, bathrooms=1,
                address_line1=address, city=city, country='Uzbekistan', base_price=40, currency='USD',
            )

        self.pricey = make('1 Pricey Street', 'Bukhara')
        self.quiet = make('2 Quiet Street', 'Khiva')
        self.service = PropertySearchService()

    def _ids(self, query):
        return {p.id for p in self.service.search({'q': query})['results']}

    def test_every_word_must_match(self):
        assert self._ids('Pricey Street') == {self.pricey.id}

    def test_words_may_match_different_fields(self):
        # "Street" is in the address, "Khiva" in the city
        assert self._ids('Street Khiva') == {self.quiet.id}

    def test_a_single_word_still_matches_every_property_containing_it(self):
        assert self._ids('Street') == {self.pricey.id, self.quiet.id}

    def test_a_word_nothing_contains_finds_nothing(self):
        assert self._ids('Street Samarkand') == set()


class ManyWordSearchCostTests(MultiWordSearchTests):
    """A05-1: one anonymous request with hundreds of words must not build one join per word."""

    def _joins(self, query):
        queryset = self.service._apply_text_search(self.service.base_queryset, query)
        return str(queryset.query).upper().count(' JOIN ')

    def test_the_number_of_joins_does_not_grow_with_the_number_of_words(self):
        few = self._joins('Street Quiet')
        many = self._joins(' '.join(f'word{n}' for n in range(150)))

        assert many == few, f'{few} joins for 2 words, {many} for 150'

    def test_words_beyond_the_eighth_are_ignored(self):
        eight_matching_words = 'Quiet Street Khiva Uzbekistan Qui Str Khi Uzb'

        assert self._ids(f'{eight_matching_words} Nowhere') == {self.quiet.id}

    def test_a_word_inside_the_first_eight_still_has_to_match(self):
        assert self._ids('Quiet Street Khiva Uzbekistan Qui Str Khi Nowhere') == set()

    def test_a_repeated_word_counts_once(self):
        assert self._ids('Quiet ' * 20 + 'Street Khiva Uzbekistan Qui Str Khi Uzb') == {self.quiet.id}
