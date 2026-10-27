"""
Refusal texts follow the page language: the site sends Accept-Language (uz, ru or en) and the API words
its validation errors in it, DRF's own texts included (DRF ships no Uzbek, so the project has its own).
"""
import pytest
from django.utils import translation

from partner.tests.test_property_create_access import (  # noqa: F401  (fixtures)
    client_for, create_requests, inventory, owner, owner_role,
)

ROOM, RATE = 1, 2
MAX_BELOW_MIN = {'min_nights': 10, 'max_nights': 2}


def refused(owner, inventory, index, language=None, **overrides):
    url, body, _ = create_requests(inventory)[index]
    extra = {'HTTP_ACCEPT_LANGUAGE': language} if language else {}
    response = client_for(owner).post(url, {**body, **overrides}, format='json', **extra)
    assert response.status_code == 400, response.data
    return response.data['error']


@pytest.mark.django_db
class TestRefusalsFollowTheLanguage:
    def test_english_is_the_default(self, owner, inventory):
        error = refused(owner, inventory, RATE, **MAX_BELOW_MIN)
        assert error['details']['max_nights'] == ['Cannot be less than the minimum nights.']

    @pytest.mark.parametrize('header', ['uz', 'uz-UZ,uz;q=0.9,en;q=0.8'])
    def test_uzbek_own_text(self, owner, inventory, header):
        error = refused(owner, inventory, RATE, header, **MAX_BELOW_MIN)
        text = "Eng ko'p kecha soni eng kam kecha sonidan kam bo'lishi mumkin emas."
        assert error['details']['max_nights'] == [text]
        assert error['message'] == f'max_nights: {text}'

    def test_russian_own_text(self, owner, inventory):
        error = refused(owner, inventory, RATE, 'ru', **MAX_BELOW_MIN)
        assert error['details']['max_nights'] == ['Максимум ночей не может быть меньше минимума.']

    def test_uzbek_drf_texts(self, owner, inventory):
        error = refused(owner, inventory, ROOM, 'uz', base_price='0', total_rooms=100000)
        assert error['details']['base_price'] == ["Qiymat 0.01 dan kam bo'lmasligi kerak."]
        assert error['details']['total_rooms'] == ["Qiymat 1000 dan oshmasligi kerak."]

    def test_russian_drf_texts(self, owner, inventory):
        error = refused(owner, inventory, ROOM, 'ru', base_price='0')
        text = error['details']['base_price'][0]
        assert 'Ensure' not in text and any('а' <= ch.lower() <= 'я' for ch in text)

    @pytest.mark.parametrize('language, text', [
        ('en', 'This field is required.'),
        ('uz', "Bu maydon to'ldirilishi shart."),
        ('ru', 'Обязательное поле.'),
    ])
    def test_required_field(self, owner, inventory, language, text):
        url, body, _ = create_requests(inventory)[ROOM]
        body.pop('name')
        response = client_for(owner).post(url, body, format='json', HTTP_ACCEPT_LANGUAGE=language)
        assert response.data['error']['details']['name'] == [text]

    def test_a_language_the_site_does_not_have_gets_english(self, owner, inventory):
        error = refused(owner, inventory, RATE, 'de', **MAX_BELOW_MIN)
        assert error['details']['max_nights'] == ['Cannot be less than the minimum nights.']

    def test_texts_with_numbers_keep_them(self, owner, inventory):
        error = refused(owner, inventory, ROOM, 'uz', max_occupancy=99)
        assert error['details']['max_occupancy'] == ["Qiymat 20 dan oshmasligi kerak."]

    def test_a_request_does_not_leave_its_language_behind(self, owner, inventory):
        refused(owner, inventory, RATE, 'uz', **MAX_BELOW_MIN)
        assert translation.get_language() in (None, 'en-us', 'en')
