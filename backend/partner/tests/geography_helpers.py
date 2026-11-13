"""Mehmanxanalardı partner API arqalı jaratatuǵın testler ushın jaylasıw payload ları."""
from geography.models import Region


def uzbek_location(region_name):
    """Jańa mehmanxana iyesi akkauntına kim ekeninen basqa kerek nárse: Ózbekstan sózligi maǵlıwmatınan regionnıń id leri
    (orın) hám sayt alatuǵın komissiya procenti."""
    region = Region.objects.select_related('country').get(country__code='UZ', name_en=region_name)
    return {'country_ref': region.country_id, 'region_ref': region.id, 'commission_percent': '2.00'}
