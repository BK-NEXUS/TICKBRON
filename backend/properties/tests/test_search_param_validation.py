"""
The search parameter rules, case by case: what is accepted, how it is cleaned, and the exact
message of every refusal. The service is checked directly, without a database.
"""
from datetime import date

import pytest

from properties.search import PropertySearchService


@pytest.fixture(scope='module')
def validate():
    service = PropertySearchService.__new__(PropertySearchService)  # no queryset needed for validation
    return service._validate_search_params


DEFAULTS = {'sort': 'relevance', 'page': 1, 'page_size': 20}


class TestAccepted:

    def test_nothing_given_gives_the_defaults(self, validate):
        assert validate({}) == DEFAULTS

    def test_query_is_trimmed_and_stripped_of_markup_characters(self, validate):
        assert validate({'q': '  <b>Grand "Hotel"</b> '})['q'] == 'bGrand Hotel/b'

    def test_blank_query_and_location_become_none(self, validate):
        result = validate({'q': '   ', 'location': ' '})

        assert result['q'] is None
        assert result['location'] is None

    def test_numbers_are_converted(self, validate):
        result = validate({
            'lat': '41.3', 'lng': '69.2', 'radius': '5', 'min_price': '10', 'max_price': '99.5',
            'min_guests': '1', 'max_guests': '4', 'property_type': '3', 'min_rating': '4', 'page': '2', 'page_size': '50',
        })

        assert result == {
            **DEFAULTS, 'lat': 41.3, 'lng': 69.2, 'radius': 5.0, 'min_price': 10.0, 'max_price': 99.5,
            'min_guests': 1, 'max_guests': 4, 'property_type': 3, 'min_rating': 4.0, 'page': 2, 'page_size': 50,
        }

    def test_one_side_of_a_pair_is_enough(self, validate):
        assert validate({'min_price': '5'})['max_price'] is None
        assert validate({'max_guests': '2'})['min_guests'] is None
        assert validate({'lat': '10'})['lng'] is None
        assert validate({'check_out': '2026-05-02'})['check_in'] is None

    def test_dates_are_parsed_from_text_or_taken_as_they_are(self, validate):
        result = validate({'check_in': '2026/05/01', 'check_out': date(2026, 5, 3)})

        assert result['check_in'] == date(2026, 5, 1)
        assert result['check_out'] == date(2026, 5, 3)

    def test_amenities_features_and_sort_pass_through(self, validate):
        result = validate({'amenities': [1, 2], 'features': ['wifi'], 'sort': 'distance'})

        assert result['amenities'] == [1, 2]
        assert result['features'] == ['wifi']
        assert result['sort'] == 'distance'


REFUSED = [
    ({'q': 'x' * 501}, 'Search query too long (max 500 characters)'),
    ({'location': 'x' * 201}, 'Location too long (max 200 characters)'),
    ({'lat': 'north'}, 'Invalid geographic coordinates: could not convert string to float: \'north\''),
    ({'lat': '91'}, 'Invalid geographic coordinates: Invalid latitude (must be between -90 and 90)'),
    ({'lng': '181'}, 'Invalid geographic coordinates: Invalid longitude (must be between -180 and 180)'),
    ({'radius': '0'}, 'Invalid radius value'),
    ({'radius': 'far'}, 'Invalid radius value'),
    ({'min_price': '-1'}, 'Invalid price values: Minimum price cannot be negative'),
    ({'max_price': '-1'}, 'Invalid price values: Maximum price cannot be negative'),
    ({'min_price': '9', 'max_price': '5'}, 'Invalid price values: Minimum price cannot be greater than maximum price'),
    ({'min_guests': '0'}, 'Invalid guest values: Minimum guests must be at least 1'),
    ({'max_guests': '0'}, 'Invalid guest values: Maximum guests must be at least 1'),
    ({'min_guests': '5', 'max_guests': '2'}, 'Invalid guest values: Minimum guests cannot be greater than maximum guests'),
    ({'amenities': 'wifi'}, 'Amenities must be a list'),
    ({'amenities': list(range(21))}, 'Too many amenities (max 20)'),
    ({'property_type': '0'}, 'Invalid property type value'),
    ({'property_type': 'hotel'}, 'Invalid property type value'),
    ({'check_in': '2026-05-03', 'check_out': '2026-05-03'}, 'Invalid date values: Check-out date must be after check-in date'),
    ({'check_in': 'tomorrow'}, 'Invalid date values: Invalid date format: tomorrow. Use YYYY-MM-DD format.'),
    ({'features': ['wifi', 'has_moat']}, 'Unknown features: has_moat'),
    ({'min_rating': 'good'}, 'Invalid minimum rating'),
    ({'min_rating': '6'}, 'Minimum rating must be between 1 and 5'),
    ({'page': '0'}, 'Invalid page number'),
    ({'page': 'one'}, 'Invalid page number'),
    ({'page_size': '101'}, 'Invalid page size'),
    ({'page_size': 'many'}, 'Invalid page size'),
]


@pytest.mark.parametrize('params, message', REFUSED)
def test_refusals_keep_their_message(validate, params, message):
    with pytest.raises(ValueError) as error:
        validate(params)

    assert str(error.value) == message


def test_unknown_sort_lists_the_valid_ones(validate):
    with pytest.raises(ValueError, match='Invalid sort method. Must be one of: .*distance'):
        validate({'sort': 'cheapest-ever'})


def test_the_first_broken_rule_is_the_one_reported(validate):
    with pytest.raises(ValueError, match='Search query too long'):
        validate({'q': 'x' * 501, 'radius': '0', 'page': '0'})
