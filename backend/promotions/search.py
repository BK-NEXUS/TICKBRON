"""Banner carousel entries for the search page: promoted hotels inside the guest's own result set."""
from promotions import service
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


def serialize_banners(request, entries):
    """Card fields of the hotel plus the `promotion_id` the frontend sends back on click."""
    items = PropertySearchResultSerializer(
        [prop for _, prop in entries], many=True, context={'rate_request': request}).data
    return [{**item, 'promotion_id': promotion.pk} for item, (promotion, _) in zip(items, entries)]


def promoted_for_home(country_id=None, limit=HOME_SLOTS):
    properties = PropertySearchService().base_queryset
    queryset = service.shown_now()
    if country_id is not None:
        queryset = queryset.filter(property__country_ref_id=country_id)
    promotions = service.ordered(queryset, limit=limit)
    by_id = properties.in_bulk([promotion.property_id for promotion in promotions])
    return [(promotion, by_id[promotion.property_id]) for promotion in promotions
            if promotion.property_id in by_id]
