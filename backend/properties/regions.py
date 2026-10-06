"""
Region of a property.

The region is stored in the existing `Property.state` field (the partner wizard
labels it "State/Region"). Geography levels for now: country (text) > region > hotel.
A full Country > Region > City dictionary is a later phase.
"""
from django.db.models import CharField, Case, IntegerField, OuterRef, Q, Subquery, Value, When
from django.db.models.functions import Coalesce, Lower, NullIf, Trim

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


def region_expression(prefix=''):
    """
    Query expression for the region of a property, UNSPECIFIED_REGION when it has none
    (NULL or blank). `prefix` is the path to Property, e.g. 'property__' from Booking.
    """
    return Coalesce(NullIf(Trim(f'{prefix}state'), Value('')), Value(UNSPECIFIED_REGION),
                    output_field=CharField())


def hotel_name_expression(prefix=''):
    """
    Query expression for a property's name, the same choice as Property.display_name():
    the English translation, else any translation, else the first address line.
    `prefix` is the path to Property, e.g. 'property__' from Booking (R12).
    """
    from properties.models import PropertyTranslation

    pk = f'{prefix}id' if prefix else 'pk'

    names = (
        PropertyTranslation.objects
        .filter(property=OuterRef(pk), is_deleted=False)
        .exclude(name='')
        .annotate(is_en=Case(When(language='en', then=Value(1)), default=Value(0),
                             output_field=IntegerField()))
        .order_by('-is_en', 'id')
        .values('name')[:1]
    )
    return Coalesce(Subquery(names, output_field=CharField()), f'{prefix}address_line1', output_field=CharField())
