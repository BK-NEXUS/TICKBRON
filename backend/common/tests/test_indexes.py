"""Indexes for the queries that run all the time: a hotel's arrivals and calendar (bookings of one property by
check-in date), the public reviews of a hotel (one property, approved, newest first) and the advertising that is
shown now (status and dates). They exist in the database itself, not only in the models."""
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
