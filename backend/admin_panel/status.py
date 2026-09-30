"""
Admin Status section: /api/v1/admin-panel/status/ (staff and super-admin only).

Countries > regions > hotels > hotel detail, plus the guests ranking (users). Lists accept
?period=all|YYYY|YYYY-MM, ?search= (inside the current list only) and
?page= / ?page_size= (20 by default, 100 at most). Definitions of counted bookings,
guests and revenue: bookings/stats.py.
"""
from django.db.models import CharField, Count, Max, Q
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from admin_panel.views import IsSuperAdminOrStaff
from bookings.stats import (
    InvalidPeriod, available_years, counted_bookings, counted_q, metric_annotations, metric_totals,
    monthly_series, parse_period, parse_year, revenue_by,
)
from properties.models import Property
from properties.regions import hotel_name_expression, region_expression
from users.models import User

TOP_COUNTRIES = 100
TOP_REGIONS = 100
TOP_HOTELS = 1000
TOP_USERS = 1000


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


@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_hotel_detail(request, property_id):
    """
    One hotel: info, owner contact, totals for ?period=, and a monthly series for ?year=
    (default: the current year).
    """
    try:
        period, date_range = parse_period(request.query_params.get('period'))
    except InvalidPeriod as error:
        return bad_request('period', error)
    try:
        year = parse_year(request.query_params.get('year'), timezone.localdate().year)
    except InvalidPeriod as error:
        return bad_request('year', error)

    prop = get_object_or_404(
        Property.objects.select_related('owner').annotate(region=region_expression(), name=hotel_name_expression()),
        pk=property_id, is_deleted=False,
    )
    owner = prop.owner
    bookings = counted_bookings().filter(property=prop)
    return Response({
        'hotel': {
            'id': prop.id, 'name': prop.name, 'status': prop.status, 'address': prop.get_full_address(),
            'city': prop.city, 'region': prop.region, 'country': prop.country,
            'registered_at': prop.created_at,
            'owner': {'id': owner.id, 'name': owner.get_full_name(), 'email': owner.email,
                      'phone': owner.phone_number},
        },
        'period': period,
        'totals': metric_totals(counted_bookings(date_range).filter(property=prop)),
        'year': year,
        'available_years': available_years(bookings),
        'monthly': monthly_series(bookings, year),
    })


@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_users(request):
    """
    Top 1000 guests by counted bookings in ?period=: name, phone, email, bookings,
    total spent (per currency) and the check-in date of their latest counted booking.
    ?search= matches first/last/full name, phone, email or ID (partial, any case).
    """
    try:
        period, date_range = parse_period(request.query_params.get('period'))
    except InvalidPeriod as error:
        return bad_request('period', error)

    counted = counted_q('bookings__', date_range)
    users = User.objects.filter(is_deleted=False)
    search = search_term(request)
    if search:
        users = users.annotate(id_text=Cast('id', CharField())).filter(
            Q(first_name__icontains=search) | Q(last_name__icontains=search)
            | Q(full_name__icontains=search) | Q(phone_number__icontains=search)
            | Q(email__icontains=search) | Q(id_text__icontains=search)
        )
    rows = (
        users.annotate(
            bookings_count=Count('bookings', filter=counted),
            last_booking_date=Max('bookings__check_in', filter=counted),
        )
        .filter(bookings_count__gt=0)
        .values('id', 'full_name', 'first_name', 'last_name', 'phone_number', 'email',
                'bookings_count', 'last_booking_date')
        .order_by('-bookings_count', '-last_booking_date', 'id')
    )
    paginator = StatusPagination()
    page = list(paginator.paginate_queryset(rows[:TOP_USERS], request))
    ids = [item['id'] for item in page]
    spent = revenue_by(counted_bookings(date_range).filter(guest_id__in=ids), 'guest_id') if ids else {}
    offset = (paginator.page.number - 1) * paginator.get_page_size(request)
    results = [
        {
            'rank': offset + index + 1,
            'id': item['id'],
            'full_name': item['full_name'] or ' '.join(filter(None, [item['first_name'], item['last_name']])),
            'first_name': item['first_name'],
            'last_name': item['last_name'],
            'phone': item['phone_number'],
            'email': item['email'],
            'bookings': item['bookings_count'],
            'total_spent': spent.get(item['id'], []),
            'last_booking_date': item['last_booking_date'].isoformat(),
        }
        for index, item in enumerate(page)
    ]
    response = paginator.get_paginated_response(results)
    response.data['period'] = period
    return response
