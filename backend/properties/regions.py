"""
Mehmanxananıń regionı.

Region bar `Property.state` maydanında saqlanadı (partner wizard onı "State/Region" dep ataydı).
Geografiya dárejeleri: mámleket > region > mehmanxana (qala ápiwayı tekst).
"""
from django.db.models import CharField, Case, IntegerField, OuterRef, Q, Subquery, Value, When
from django.db.models.functions import Coalesce, Lower, NullIf, Trim

# Regionı joq mehmanxanalar ushın belgi (Status view leri olardı sonıń astında toparlaydı)
UNSPECIFIED_REGION = 'Unspecified'

# Regionı anıq bolǵan qalalar: regionlıq oray regionǵa óz atın beredi
CITY_REGIONS = {
    'tashkent': 'Tashkent',
    'samarkand': 'Samarkand',
    'bukhara': 'Bukhara',
}


def backfill_regions_from_city(property_model):
    """
    Anıq qaladaǵı regionı joq mehmanxanalardıń regionın belgilew.

    Data migration lar óz tariyxıy modelin bere alıwı ushın model klasın aladı.
    Aldınan belgilengen regionnıń ústinen hesh qashan jazılmaydı. Jańalanǵan qatarlar sanın qaytaradı.
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
    Mehmanxana regionı ushın query ańlatpası, regionı joq bolsa (NULL yamasa bos) UNSPECIFIED_REGION.
    `prefix` Property ge jol, mısalı Booking ten 'property__'.
    """
    return Coalesce(NullIf(Trim(f'{prefix}state'), Value('')), Value(UNSPECIFIED_REGION),
                    output_field=CharField())


def hotel_name_expression(prefix=''):
    """
    Mehmanxana atı ushın query ańlatpası, Property.display_name() penen birdey tańlaw:
    inglizsha awdarma, bolmasa qálegen awdarma, bolmasa birinshi mánzil qatarı.
    `prefix` Property ge jol, mısalı Booking ten 'property__' (R12).
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
