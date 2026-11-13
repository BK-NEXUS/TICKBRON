"""
Mehmanxana jaylasıwın Geography sózligine qarsı tekseriw (reje G4).

GeographyRefsMixin country_ref, region_ref di dizimlegen Property ModelSerializer ge qosıladı. Ol
tańlanǵan qatarlardıń aktiv ekenin, regionnıń mámleket ishinde ekenin hám
jańa mehmanxananıń ekewin de alatuǵının tekseredi.
"""
from rest_framework import serializers

REF_FIELDS = ('country_ref', 'region_ref')


def check_geography(incoming, current=None, required=False, nullable=False):
    """
    `incoming` degi (tekserilgen maǵlıwmat) geografiya ref leri ushın {field: message} qaytaradı.

    current:  ózgertilip atırǵan mehmanxana (jaratıwda None); jiberilmegen ref ler sonnan oqıladı.
    required: ekewi de jiberilgen bolıwı kerek (jaratıw).
    nullable: ekewi birge null bola aladı (admin jaylasıwdı tazalaǵanda).
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

    if nullable and all(incoming.get(field) is None for field in sent) and len(sent) == len(REF_FIELDS):
        return errors

    merged = {field: incoming[field] if field in incoming else getattr(current, field, None)
              for field in REF_FIELDS}
    for field in REF_FIELDS:
        if merged[field] is None:
            errors[field] = 'Country and region must be set together.'
        elif field in incoming and not merged[field].is_active:
            errors[field] = 'This location is hidden and cannot be chosen.'
    if errors:
        return errors

    country, region = (merged[field] for field in REF_FIELDS)
    if region.country_id != country.pk:
        errors['region_ref'] = 'This region is not in the chosen country.'
    return errors


class GeographyRefsMixin:
    """
    Partner stili qaǵıyda: ref ler jaratıwda májbúriy hám ózgertiliwi múmkin, tazalanbaydı.

    Eski tekst maydanlar country / state / city kirisiw emes (olar inglizsha atlardıń tek oqıw nusqaları,
    Property.save() toltıradı); tek id ler esapqa alınadı. Regiondan tómen qala yamasa tuman joq.
    """

    def validate(self, attrs):
        attrs = super().validate(attrs)
        errors = check_geography(attrs, current=self.instance, required=self.instance is None)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs
