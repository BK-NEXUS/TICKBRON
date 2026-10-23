"""Banner carousel entries for the search page: promoted hotels inside the guest's own result set."""
from collections import defaultdict

from promotions import service
from promotions.models import PromotionPhoto
from properties.models import PropertyPhoto
from properties.search import PropertySearchService
from properties.serializers import PropertySearchResultSerializer

SEARCH_SLOTS = 8
HOME_SLOTS = 8


def promoted_for_search(search_service, search_params, limit=SEARCH_SLOTS):
    """
    `[(promotion, property)]` in display order. The promoted ids are intersected with the
    filtered queryset the guest asked for, so a hotel that does not match is never added.
    """
    matching_ids = search_service.filtered_queryset(search_params).order_by().values('id')
    promotions = service.ordered(service.shown_now().filter(property_id__in=matching_ids), limit=limit)
    if not promotions:
        return []
    properties = search_service.base_queryset.in_bulk([promotion.property_id for promotion in promotions])
    return [(promotion, properties[promotion.property_id]) for promotion in promotions
            if promotion.property_id in properties]


def _banner_photos(entries):
    """
    `{promotion_id: [url, ...]}`, at most service.MAX_PHOTOS each: the pictures put on the ad, else the hotel's own
    photos with the cover first. Two queries for the whole carousel.
    """
    own = defaultdict(list)
    for row in PromotionPhoto.objects.filter(
            promotion_id__in=[promotion.pk for promotion, _ in entries], is_deleted=False, is_active=True):
        own[row.promotion_id].append(row.photo.url)
    hotel = defaultdict(list)
    for row in PropertyPhoto.objects.filter(
            property_id__in=[prop.pk for _, prop in entries], is_deleted=False, is_active=True,
    ).order_by('-is_primary', 'display_order', 'id'):
        hotel[row.property_id].append(row.photo.url)
    return {promotion.pk: (own[promotion.pk] or hotel[prop.pk])[:service.MAX_PHOTOS] for promotion, prop in entries}


def serialize_banners(request, entries):
    """Card fields of the hotel, the `promotion_id` the frontend sends back on click and the `promo_photos`."""
    items = PropertySearchResultSerializer(
        [prop for _, prop in entries], many=True, context={'rate_request': request}).data
    photos = _banner_photos(entries)
    return [{**item, 'promotion_id': promotion.pk, 'promo_photos': photos[promotion.pk]}
            for item, (promotion, _) in zip(items, entries)]


def promoted_for_home(country_id=None, limit=HOME_SLOTS):
    properties = PropertySearchService().base_queryset
    queryset = service.shown_now()
    if country_id is not None:
        queryset = queryset.filter(property__country_ref_id=country_id)
    promotions = service.ordered(queryset, limit=limit)
    by_id = properties.in_bulk([promotion.property_id for promotion in promotions])
    return [(promotion, by_id[promotion.property_id]) for promotion in promotions
            if promotion.property_id in by_id]
