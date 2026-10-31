"""Location payloads for tests that create properties through the partner API."""
from geography.models import City


def uzbek_location(city_name):
    """What a new hotel-owner account needs besides who it is: the ids of a city from the Uzbekistan dictionary
    data (the place) and the commission percent the site takes."""
    city = City.objects.select_related('region__country').get(region__country__code='UZ', name_en=city_name)
    return {'country_ref': city.region.country_id, 'region_ref': city.region_id, 'city_ref': city.id,
            'commission_percent': '2.00'}
