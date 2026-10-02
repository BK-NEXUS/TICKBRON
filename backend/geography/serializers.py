"""
Validation of a property's location against the Geography dictionary (plan G4).

GeographyRefsMixin goes on a Property ModelSerializer that lists country_ref,
region_ref and city_ref. It checks that the chosen rows are active, that the
region is inside the country and the city inside the region, and that a new
property gets all three.
"""
from rest_framework import serializers

from geography.mapping import GeographyIndex
from geography.models import City, Country, Region

REF_FIELDS = ('country_ref', 'region_ref', 'city_ref')
TEXT_FIELDS = ('country', 'state', 'city')  # DEPRECATED input, see resolve_text_location


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


def resolve_text_location(text, current=None):
    """
    DEPRECATED (2026-10-02, remove after the frontend moves to ids, G5-G6): resolve the old text
    fields country / state / city to dictionary rows through the geography mapping.

    text:    the text fields sent by the client ({'country': ..., 'city': ...}, any subset).
    current: the property being edited; text that was not sent is read from it.
    Returns ({'country_ref', 'region_ref', 'city_ref'}, {}) or ({}, {field: message}). Country and
    city must match; the region comes from the city, so `state` never causes an error.
    """
    merged = {field: text[field] if field in text else getattr(current, field, None) for field in TEXT_FIELDS}
    country, region, city = GeographyIndex(Country, Region, City).match(
        merged['country'], merged['state'], merged['city'])
    if country is None:
        shown = merged['country'] or ''
        return {}, {'country': f'Country "{shown}" was not found. Choose it with country_ref.'}
    if city is None:
        shown = merged['city'] or ''
        return {}, {'city': f'City "{shown}" was not found in {country.name_en}. Choose it with city_ref.'}
    return {'country_ref': country, 'region_ref': region, 'city_ref': city}, {}


class GeographyRefsMixin:
    """
    Partner-style rule: refs are required on create and can be changed, not cleared.

    DEPRECATED compatibility: instead of the ids a client may still send the old text fields
    country / state / city. They are resolved to refs; ids win when both are sent, and text
    equal to what the property already has is ignored.
    """

    def validate(self, attrs):
        attrs = super().validate(attrs)
        text = {field: attrs.pop(field) for field in TEXT_FIELDS if field in attrs}
        if text and not any(field in attrs for field in REF_FIELDS):
            unchanged = self.instance is not None and all(
                (value or None) == (getattr(self.instance, field, None) or None) for field, value in text.items())
            if not unchanged:
                refs, errors = resolve_text_location(text, self.instance)
                if errors:
                    raise serializers.ValidationError(errors)
                attrs.update(refs)
        errors = check_geography(attrs, current=self.instance, required=self.instance is None)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs
