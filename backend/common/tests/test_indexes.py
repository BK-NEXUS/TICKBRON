"""Hár waqıt isleytuǵın query ler ushın indekslar: mehmanxananıń keliwleri hám kalendarı (bir mehmanxananıń bronları
kiriw sanası boyınsha), mehmanxananıń ashıq sharhları (bir mehmanxana, tastıyıqlanǵan, eń jańası birinshi) hám házir
kórsetiletuǵın reklama (status hám sanalar). Olar tek model lerde emes, database tiń ózinde bar."""
import pytest
from django.apps import apps
from django.db import connection

pytestmark = pytest.mark.django_db

EXPECTED = [
    ('bookings.Booking', ['property_id', 'check_in']),
    ('accounts.Review', ['property_id', 'status', 'created_at']),
    ('promotions.Promotion', ['status', 'start_date', 'end_date']),
]


def indexed_columns(model):
    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(cursor, model._meta.db_table)
    return [details['columns'] for details in constraints.values() if details['index']]


@pytest.mark.parametrize('label,columns', EXPECTED)
def test_the_database_has_the_index(label, columns):
    assert columns in indexed_columns(apps.get_model(label))
