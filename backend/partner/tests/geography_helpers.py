"""Location payloads for tests that create properties through the partner API."""
from geography.models import City


def uzbek_location(city_name):
    """country_ref / region_ref / city_ref ids of a city from the Uzbekistan dictionary data."""
    city = City.objects.select_related('region__country').get(region__country__code='UZ', name_en=city_name)
    return {'country_ref': city.region.country_id, 'region_ref': city.region_id, 'city_ref': city.id}
