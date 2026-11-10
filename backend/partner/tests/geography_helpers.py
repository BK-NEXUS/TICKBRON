"""Location payloads for tests that create properties through the partner API."""
from geography.models import Region


def uzbek_location(region_name):
    """What a new hotel-owner account needs besides who it is: the ids of a region from the Uzbekistan dictionary
    data (the place), the town typed as text (a hotel needs one) and the commission percent the site takes."""
    region = Region.objects.select_related('country').get(country__code='UZ', name_en=region_name)
    return {'country_ref': region.country_id, 'region_ref': region.id, 'city': f'{region_name} Town',
            'commission_percent': '2.00'}
