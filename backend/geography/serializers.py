"""
Validation of a property's location against the Geography dictionary (plan G4).

GeographyRefsMixin goes on a Property ModelSerializer that lists country_ref,
region_ref and city_ref. It checks that the chosen rows are active, that the
region is inside the country and the city inside the region, and that a new
property gets all three.
"""
from rest_framework import serializers

REF_FIELDS = ('country_ref', 'region_ref', 'city_ref')


def check_geography(incoming, current=None, required=False, nullable=False):
    """
    Return {field: message} for the geography refs in `incoming` (validated data).

    current:  the property being edited (None on create); refs not sent are read from it.
    required: all three refs must be sent (create).
    nullable: all three may be null together (admin clearing the location).
    """
    errors = {}
    if required:
        for field in REF_FIELDS:
            if field not in incoming:
                errors[field] = 'This field is required.'
        if errors:
            return errors

    sent = [field for field in REF_FIELDS if field in incoming]
    if not sent:
        return errors

    if nullable and all(incoming.get(field) is None for field in sent) and len(sent) == 3:
        return errors

    merged = {field: incoming[field] if field in incoming else getattr(current, field, None)
              for field in REF_FIELDS}
    for field in REF_FIELDS:
        if merged[field] is None:
            errors[field] = 'Country, region and city must be set together.'
        elif field in incoming and not merged[field].is_active:
            errors[field] = 'This location is hidden and cannot be chosen.'
    if errors:
        return errors

    country, region, city = (merged[field] for field in REF_FIELDS)
    if region.country_id != country.pk:
        errors['region_ref'] = 'This region is not in the chosen country.'
    elif city.region_id != region.pk:
        errors['city_ref'] = 'This city is not in the chosen region.'
    return errors


class GeographyRefsMixin:
    """Partner-style rule: refs are required on create and can be changed, not cleared."""

    def validate(self, attrs):
        attrs = super().validate(attrs)
        errors = check_geography(attrs, current=self.instance, required=self.instance is None)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs
