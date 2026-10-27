"""A new server has no property types, and a hotel cannot be created without one: the command adds the standard ones."""
import pytest
from django.core.management import call_command

from properties.models import PropertyType

STANDARD = {'hotel', 'hostel', 'guest-house', 'apartment', 'resort'}


@pytest.mark.django_db
def test_adds_the_standard_types_to_an_empty_database():
    call_command('seed_property_types')
    assert set(PropertyType.objects.values_list('slug', flat=True)) == STANDARD


@pytest.mark.django_db
def test_running_it_again_changes_nothing():
    call_command('seed_property_types')
    ids = sorted(PropertyType.objects.values_list('id', flat=True))
    call_command('seed_property_types')
    assert sorted(PropertyType.objects.values_list('id', flat=True)) == ids


@pytest.mark.django_db
def test_keeps_a_type_that_already_exists_under_the_same_slug():
    PropertyType.objects.create(name='Apartment', slug='apartment', description='made by hand')
    call_command('seed_property_types')
    assert PropertyType.objects.get(slug='apartment').description == 'made by hand'
    assert PropertyType.objects.count() == len(STANDARD)
