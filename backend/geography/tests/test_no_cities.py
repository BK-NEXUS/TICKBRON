"""Geografiyanıń qala dárejesi joq (reje .ai/PLAN_GEO_REMOVE_CITY.md): tek mámleket hám region sózlikler,
mehmanxananıń qalası ápiwayı tekst."""
import pytest
from rest_framework.test import APIClient

from geography import models as geography_models
from geography.models import Region
from properties.models import Property
from promotions.models import Promotion

pytestmark = pytest.mark.django_db


def field_names(model):
    return {field.name for field in model._meta.get_fields()}


def test_the_city_dictionary_is_gone():
    assert not hasattr(geography_models, 'City')
    assert not hasattr(Region, 'cities')


def test_a_hotel_keeps_its_town_as_text_and_has_no_city_reference():
    names = field_names(Property)
    assert 'city' in names
    assert 'city_ref' not in names
    assert {'country_ref', 'region_ref'} <= names


def test_an_advertisement_is_scoped_by_country_or_region_only():
    assert 'city_ref' not in field_names(Promotion)


def test_the_public_list_of_cities_is_gone():
    region = Region.objects.first()
    assert APIClient().get(f'/api/v1/geography/regions/{region.pk}/cities/').status_code == 404


def test_the_admin_routes_of_cities_are_gone():
    client = APIClient()
    assert client.get('/api/v1/admin-panel/geography/cities/').status_code == 404
    assert client.get('/api/v1/admin-panel/geography/cities/1/').status_code == 404
