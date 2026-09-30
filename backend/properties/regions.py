"""
Region of a property.

The region is stored in the existing `Property.state` field (the partner wizard
labels it "State/Region"). Geography levels for now: country (text) > region > hotel.
A full Country > Region > City dictionary is a later phase.
"""
from django.db.models import Q
from django.db.models.functions import Lower, Trim

# Label for hotels without a region (Status views group them under it)
UNSPECIFIED_REGION = 'Unspecified'

# Cities whose region is obvious: the regional centre gives the region its name
CITY_REGIONS = {
    'tashkent': 'Tashkent',
    'samarkand': 'Samarkand',
    'bukhara': 'Bukhara',
}


def backfill_regions_from_city(property_model):
    """
    Set the region of properties in an obvious city when they have none.

    Takes the model class so data migrations can pass their historical model.
    Never overwrites a region that is already set. Returns the number of rows updated.
    """
    no_region = Q(state__isnull=True) | Q(state__regex=r'^\s*$')
    updated = 0
    for city, region in CITY_REGIONS.items():
        updated += (
            property_model.objects
            .annotate(city_key=Lower(Trim('city')))
            .filter(no_region, city_key=city)
            .update(state=region)
        )
    return updated
