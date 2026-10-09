"""Banner carousel entries for the search page: promoted hotels inside the guest's own result set."""
from promotions import service

SEARCH_SLOTS = 8


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
