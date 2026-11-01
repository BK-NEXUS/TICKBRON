"""The alphabet filter helpers: which names land under which letter."""
import pytest
from django.test import RequestFactory
from rest_framework.exceptions import ValidationError

from common import alphabet
from promotions.tests.helpers import make_hotel, make_owner
from properties.models import Property, PropertyTranslation
from users.models import User

pytestmark = pytest.mark.django_db


def request_with(letter=None):
    return RequestFactory().get('/x/', {} if letter is None else {'letter': letter})


def drf(request):
    from rest_framework.request import Request
    return Request(request)


class TestLetterFromRequest:
    @pytest.mark.parametrize('raw, expected', [
        (None, None), ('', None), ('   ', None), ('a', 'A'), ('A', 'A'), (' b ', 'B'), ('#', '#'),
        ('Я', 'Я'), ('я', 'Я'), ('Ў', 'Ў'), ('ў', 'Ў'),
    ])
    def test_a_good_letter_is_normalised(self, raw, expected):
        assert alphabet.letter_from(drf(request_with(raw))) == expected

    @pytest.mark.parametrize('raw', ['ab', '1', '%', '_', '*', 'a,b', '  ab ', "'", '1' * 50, '‮'])
    def test_anything_else_is_refused(self, raw):
        with pytest.raises(ValidationError):
            alphabet.letter_from(drf(request_with(raw)))


def person(email, **fields):
    return User.objects.create_user(email=email, password='Kitob7$yy', **fields)


class TestPeople:
    @pytest.fixture
    def people(self):
        return {
            'full': person('p1@example.com', full_name='Aziz Karimov'),
            'lower': person('p2@example.com', full_name='anvar tosh'),
            'parts': person('p3@example.com', first_name='Bobur', last_name='Aliev'),
            'last_only': person('p4@example.com', last_name='Davlatov'),
            'email_only': person('carol@example.com'),
            'cyrillic': person('p6@example.com', full_name='Азиз Каримов'),
            'cyrillic_lower': person('p7@example.com', full_name='азиз тошев'),
            'digit': person('p8@example.com', full_name='1st Guest'),
            'quote': person('p9@example.com', full_name='"Quoted" Name'),
        }

    def ids(self, letter):
        return set(alphabet.people_with_letter(User.objects.all(), letter).values_list('email', flat=True))

    def test_no_letter_changes_nothing(self, people):
        assert alphabet.people_with_letter(User.objects.all(), None).count() == User.objects.count()

    def test_a_letter_finds_the_shown_name_in_either_case(self, people):
        assert self.ids('A') == {'p1@example.com', 'p2@example.com'}

    def test_a_person_without_a_full_name_is_found_by_the_first_name(self, people):
        assert self.ids('B') == {'p3@example.com'}

    def test_a_person_with_only_a_last_name_is_found_by_it(self, people):
        assert self.ids('D') == {'p4@example.com'}

    def test_a_person_without_any_name_is_found_by_the_address(self, people):
        assert self.ids('C') == {'carol@example.com'}

    def test_cyrillic_letters_work_in_both_cases(self, people):
        assert self.ids('А') == {'p6@example.com', 'p7@example.com'}

    def test_the_hash_collects_names_that_do_not_start_with_a_letter(self, people):
        assert self.ids('#') == {'p8@example.com', 'p9@example.com'}

    def test_every_person_is_under_exactly_one_letter(self, people):
        letters = {chr(code) for code in range(ord('A'), ord('Z') + 1)} | {'А', '#'}
        seen = [email for letter in letters for email in self.ids(letter)]
        assert sorted(seen) == sorted(User.objects.values_list('email', flat=True))


class TestHotels:
    def named(self, owner, *names, **extra):
        hotel = make_hotel(owner, name=names[0], **extra)
        for language, name in zip(('uz', 'ru'), names[1:]):
            PropertyTranslation.objects.create(property=hotel, language=language, name=name)
        return hotel

    def ids(self, letter):
        return set(alphabet.hotels_with_letter(Property.objects.all(), letter).values_list('id', flat=True))

    def test_a_hotel_is_found_by_its_name_in_any_language(self):
        owner = make_owner('hotelier@example.com')
        grand = self.named(owner, 'Grand Hotel', 'Гранд')
        registan = self.named(owner, 'Registan Palace', 'Регистан')

        assert self.ids('G') == {grand.id} and self.ids('Г') == {grand.id}
        assert self.ids('R') == {registan.id} and self.ids('Р') == {registan.id}

    def test_a_hotel_with_two_matching_names_is_listed_once(self):
        owner = make_owner('hotelier@example.com')
        hotel = self.named(owner, 'Alpha', 'Alfa')

        found = alphabet.hotels_with_letter(Property.objects.all(), 'A')

        assert list(found.values_list('id', flat=True)) == [hotel.id]

    def test_the_hash_collects_names_that_do_not_start_with_a_letter(self):
        owner = make_owner('hotelier@example.com')
        odd = self.named(owner, '5 Stars Inn')
        self.named(owner, 'Normal Inn')

        assert self.ids('#') == {odd.id}

    def test_no_letter_changes_nothing(self):
        make_hotel(make_owner('hotelier@example.com'), name='Any')
        assert alphabet.hotels_with_letter(Property.objects.all(), None).count() == 1
