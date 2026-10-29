"""How guests rate the owner's hotels: the approved reviews only, over all time (not the period the page shows)."""
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Avg, Count

from accounts.models import Review

CATEGORIES = ('cleanliness', 'location', 'value', 'amenities', 'service')
STARS = (1, 2, 3, 4, 5)


def _approved(property_ids):
    return Review.objects.filter(property_id__in=property_ids, status='approved', is_deleted=False)


def _one_decimal(value):
    """4.25 -> '4.3' (halves go up, as people count); None stays None."""
    if value is None:
        return None
    return str(Decimal(str(value)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


def ratings_by_hotel(property_ids):
    """{hotel id: {'count', 'average'}} for every id asked for (a hotel without reviews: 0 and None)."""
    rows = {row['property_id']: row for row in _approved(property_ids).values('property_id').annotate(
        count=Count('id'), average=Avg('overall_rating')).order_by()}
    return {
        property_id: {
            'count': rows[property_id]['count'] if property_id in rows else 0,
            'average': _one_decimal(rows[property_id]['average']) if property_id in rows else None,
        }
        for property_id in property_ids
    }


def rating_detail(property_id):
    """One hotel: count, average, how many reviews gave 1..5 stars, and the average of each category."""
    reviews = _approved([property_id])
    by_stars = dict(reviews.values_list('overall_rating').annotate(total=Count('id')).order_by())
    totals = reviews.aggregate(count=Count('id'), average=Avg('overall_rating'),
                               **{name: Avg(f'{name}_rating') for name in CATEGORIES})
    return {
        'count': totals['count'], 'average': _one_decimal(totals['average']),
        'distribution': [by_stars.get(stars, 0) for stars in STARS],
        'categories': {name: _one_decimal(totals[name]) for name in CATEGORIES},
    }
