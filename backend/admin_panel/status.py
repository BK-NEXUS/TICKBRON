"""
Admin Status section: /api/v1/admin-panel/status/ (staff and super-admin only).

Countries > regions > hotels > hotel detail, plus the guests ranking. Lists accept
?period=all|YYYY|YYYY-MM, ?search= (inside the current list only) and
?page= / ?page_size= (20 by default, 100 at most). Definitions of counted bookings,
guests and revenue: bookings/stats.py.
"""
from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from admin_panel.views import IsSuperAdminOrStaff
from bookings.stats import InvalidPeriod, counted_bookings, metric_annotations, parse_period, revenue_by
from properties.models import Property
from properties.regions import hotel_name_expression, region_expression

TOP_COUNTRIES = 100
TOP_REGIONS = 100
TOP_HOTELS = 1000


class StatusPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def bad_request(field, error):
    return Response({field: [str(error)]}, status=status.HTTP_400_BAD_REQUEST)


def search_term(request):
    return (request.query_params.get('search') or '').strip()


def ranked_page(request, rows, limit, key, bookings, booking_key, to_row, extra):
    """
    One page of the top `limit` grouped rows, ranked, with per-currency revenue.

    `rows` are ordered, aggregated dicts; revenue is aggregated for the keys on this
    page only (`bookings` = counted bookings, `booking_key` = the same key seen from Booking).
    """
    paginator = StatusPagination()
    page = list(paginator.paginate_queryset(rows[:limit], request))
    keys = [item[key] for item in page]
    revenue = revenue_by(bookings.filter(**{f'{booking_key}__in': keys}), booking_key) if keys else {}
    offset = (paginator.page.number - 1) * paginator.get_page_size(request)
    results = [
        {
            'rank': offset + index + 1,
            **to_row(item),
            'bookings': item['bookings_count'],
            'guests': item['guests_count'],
            'revenue': revenue.get(item[key], []),
        }
        for index, item in enumerate(page)
    ]
    response = paginator.get_paginated_response(results)
    response.data.update(extra)
    return response


@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_countries(request):
    """Top 100 countries by counted bookings: bookings, guests, revenue, hotel count."""
    try:
        period, date_range = parse_period(request.query_params.get('period'))
    except InvalidPeriod as error:
        return bad_request('period', error)

    properties = Property.objects.filter(is_deleted=False)
    search = search_term(request)
    if search:
        properties = properties.filter(country__icontains=search)
    rows = (
        properties.values('country')
        .annotate(hotels_count=Count('id', distinct=True), **metric_annotations('bookings__', date_range))
        .order_by('-bookings_count', '-guests_count', 'country')
    )
    bookings = counted_bookings(date_range).filter(property__is_deleted=False)
    return ranked_page(
        request, rows, TOP_COUNTRIES, 'country', bookings, 'property__country',
        lambda item: {'country': item['country'], 'hotels': item['hotels_count']},
        {'period': period},
    )


@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_regions(request, country):
    """Top 100 regions of one country; hotels without a region are grouped as "Unspecified"."""
    try:
        period, date_range = parse_period(request.query_params.get('period'))
    except InvalidPeriod as error:
        return bad_request('period', error)

    properties = Property.objects.filter(is_deleted=False, country=country).annotate(region=region_expression())
    search = search_term(request)
    if search:
        properties = properties.filter(region__icontains=search)
    rows = (
        properties.values('region')
        .annotate(hotels_count=Count('id', distinct=True), **metric_annotations('bookings__', date_range))
        .order_by('-bookings_count', '-guests_count', 'region')
    )
    bookings = (
        counted_bookings(date_range)
        .filter(property__is_deleted=False, property__country=country)
        .annotate(region=region_expression('property__'))
    )
    return ranked_page(
        request, rows, TOP_REGIONS, 'region', bookings, 'region',
        lambda item: {'region': item['region'], 'hotels': item['hotels_count']},
        {'period': period, 'country': country},
    )


@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_hotels(request, country, region):
    """Top 1000 hotels of one region ("Unspecified" = hotels without a region)."""
    try:
        period, date_range = parse_period(request.query_params.get('period'))
    except InvalidPeriod as error:
        return bad_request('period', error)

    properties = (
        Property.objects.filter(is_deleted=False, country=country)
        .annotate(region=region_expression(), name=hotel_name_expression())
        .filter(region=region)
    )
    search = search_term(request)
    if search:
        properties = properties.filter(name__icontains=search)
    rows = (
        properties.values('id', 'name', 'city', 'status')
        .annotate(**metric_annotations('bookings__', date_range))
        .order_by('-bookings_count', '-guests_count', 'name', 'id')
    )
    bookings = counted_bookings(date_range).filter(property__is_deleted=False)
    return ranked_page(
        request, rows, TOP_HOTELS, 'id', bookings, 'property_id',
        lambda item: {'id': item['id'], 'name': item['name'], 'city': item['city'], 'status': item['status']},
        {'period': period, 'country': country, 'region': region},
    )
