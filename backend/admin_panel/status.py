"""
Admin Status section: /api/v1/admin-panel/status/ (staff and super-admin only).

Countries > regions > hotels > hotel detail, plus the guests ranking (users). Hotels are grouped by
their Geography refs: a country by its ISO code, a region by its id, and hotels without the ref under
"unspecified" in the URL and "Unspecified" in the label. Lists accept
?period=all|YYYY|YYYY-MM, ?search= (inside the current list only) and
?page= / ?page_size= (20 by default, 100 at most). Definitions of counted bookings,
guests and revenue: bookings/stats.py.
"""
from django.db.models import CharField, Count, Max, Q, Value
from django.db.models.functions import Cast, Coalesce
from django.shortcuts import get_object_or_404
from common.dates import business_today
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from admin_panel.models import AdminAccessLog
from admin_panel.views import IsSuperAdminOrStaff
from bookings.stats import (
    InvalidPeriod, available_years, counted_bookings, counted_q, metric_annotations, metric_totals,
    monthly_series, parse_period, parse_year, revenue_by,
)
from geography.models import Country, Region
from properties.models import Property
from properties.regions import UNSPECIFIED_REGION, hotel_name_expression
from users.models import User

TOP_COUNTRIES = 100
TOP_REGIONS = 100
TOP_HOTELS = 1000
TOP_USERS = 1000


class StatusPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


UNSPECIFIED = 'unspecified'  # URL segment and group key of hotels without a country / region ref


def country_key(prefix=''):
    """Group key of a hotel's country: ISO code, or UNSPECIFIED. `prefix`: path to Property."""
    return Coalesce(f'{prefix}country_ref__code', Value(UNSPECIFIED), output_field=CharField())


def region_key(prefix=''):
    """Group key of a hotel's region: the region id as text, or UNSPECIFIED."""
    return Coalesce(Cast(f'{prefix}region_ref_id', CharField()), Value(UNSPECIFIED), output_field=CharField())


def _alias_q(base, value):
    """Q matching the uz, ru or en name (case-insensitive) behind `base` (e.g. 'country_ref__' or '')."""
    return (Q(**{f'{base}name_en__iexact': value}) | Q(**{f'{base}name_uz__iexact': value})
            | Q(**{f'{base}name_ru__iexact': value}))


def is_iso_code(value):
    return len(value) == 2 and value.isascii() and value.isalpha()


def country_q(segment, path):
    """
    Q for the country named by a URL segment, behind the relation `path` ('country_ref',
    'property__country_ref'; '' when the query is on Country itself).

    The segment is an ISO code (any case) or "unspecified" (no country).
    DEPRECATED (2026-10-02, until the frontend moves to codes, G5-G6): it may also be a country name
    in any language, the value the old lists gave as `country`.
    """
    base = f'{path}__' if path else ''
    if segment.lower() == UNSPECIFIED:
        return Q(**{f'{path}__isnull': True}) if path else Q(pk__in=[])
    if is_iso_code(segment):
        return Q(**{f'{base}code': segment.upper()})
    return _alias_q(base, segment)


def region_q(segment, path):
    """
    Q for the region named by a URL segment, behind `path` ('region_ref'; '' on Region itself).

    The segment is a region id or "unspecified" (no region).
    DEPRECATED (2026-10-02, until the frontend moves to ids, G5-G6): it may also be a region name in
    any language, the value the old lists gave as `region`.
    """
    base = f'{path}__' if path else ''
    if segment.lower() == UNSPECIFIED:
        return Q(**{f'{path}__isnull': True}) if path else Q(pk__in=[])
    if segment.isdigit():
        return Q(**{f'{path}_id': int(segment)}) if path else Q(pk=int(segment))
    return _alias_q(base, segment)


def country_filter(segment, prefix=''):
    return country_q(segment, f'{prefix}country_ref')


def region_filter(segment, prefix=''):
    return region_q(segment, f'{prefix}region_ref')


def echo_key(segment):
    """The key as the response reports it: codes upper-case, "unspecified" lower-case, names as sent."""
    if segment.lower() == UNSPECIFIED:
        return UNSPECIFIED
    return segment.upper() if is_iso_code(segment) else segment


def names_filter(prefix, term):
    """Q matching the term in the uz, ru or en name behind `prefix` (e.g. 'country_ref__')."""
    return (Q(**{f'{prefix}name_uz__icontains': term}) | Q(**{f'{prefix}name_ru__icontains': term})
            | Q(**{f'{prefix}name_en__icontains': term}))


def names(item, prefix):
    """uz/ru/en names of a grouped row; "Unspecified" in all three when the group has no ref."""
    return {language: item[f'{prefix}name_{language}'] or UNSPECIFIED_REGION for language in ('uz', 'ru', 'en')}


def country_name(segment):
    """English name for the breadcrumb; None for a country that does not exist."""
    if segment.lower() == UNSPECIFIED:
        return UNSPECIFIED_REGION
    return Country.objects.filter(country_q(segment, '')).values_list('name_en', flat=True).first()


def region_name(country, region):
    """English name of the region inside the country; None when there is no such region."""
    if region.lower() == UNSPECIFIED:
        return UNSPECIFIED_REGION
    return (Region.objects.filter(region_q(region, ''), country_q(country, 'country'))
            .values_list('name_en', flat=True).first())


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


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_countries(request):
    """Top 100 countries by counted bookings: bookings, guests, revenue, hotel count."""
    try:
        period, date_range = parse_period(request.query_params.get('period'))
    except InvalidPeriod as error:
        return bad_request('period', error)

    properties = Property.objects.filter(is_deleted=False).annotate(country_key=country_key())
    search = search_term(request)
    if search:
        properties = properties.filter(names_filter('country_ref__', search) | Q(country_ref__code__iexact=search))
    rows = (
        properties.values('country_key', 'country_ref__name_uz', 'country_ref__name_ru', 'country_ref__name_en')
        .annotate(hotels_count=Count('id', distinct=True), **metric_annotations('bookings__', date_range))
        .order_by('-bookings_count', '-guests_count', 'country_ref__name_en', 'country_key')
    )
    bookings = (
        counted_bookings(date_range).filter(property__is_deleted=False)
        .annotate(country_key=country_key('property__'))
    )

    def to_row(item):
        name = names(item, 'country_ref__')
        return {
            'code': None if item['country_key'] == UNSPECIFIED else item['country_key'],
            'country': name['en'], 'name_uz': name['uz'], 'name_ru': name['ru'], 'name_en': name['en'],
            'hotels': item['hotels_count'],
        }

    return ranked_page(request, rows, TOP_COUNTRIES, 'country_key', bookings, 'country_key', to_row,
                       {'period': period})


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_regions(request, country):
    """Top 100 regions of one country; hotels without a region are grouped as "Unspecified"."""
    try:
        period, date_range = parse_period(request.query_params.get('period'))
    except InvalidPeriod as error:
        return bad_request('period', error)

    properties = (
        Property.objects.filter(country_filter(country), is_deleted=False).annotate(region_key=region_key())
    )
    search = search_term(request)
    if search:
        properties = properties.filter(names_filter('region_ref__', search))
    rows = (
        properties.values('region_key', 'region_ref__name_uz', 'region_ref__name_ru', 'region_ref__name_en')
        .annotate(hotels_count=Count('id', distinct=True), **metric_annotations('bookings__', date_range))
        .order_by('-bookings_count', '-guests_count', 'region_ref__name_en', 'region_key')
    )
    bookings = (
        counted_bookings(date_range)
        .filter(country_filter(country, 'property__'), property__is_deleted=False)
        .annotate(region_key=region_key('property__'))
    )

    def to_row(item):
        name = names(item, 'region_ref__')
        return {
            'id': None if item['region_key'] == UNSPECIFIED else int(item['region_key']),
            'region': name['en'], 'name_uz': name['uz'], 'name_ru': name['ru'], 'name_en': name['en'],
            'hotels': item['hotels_count'],
        }

    extra = {'period': period, 'country': echo_key(country)}
    response = ranked_page(request, rows, TOP_REGIONS, 'region_key', bookings, 'region_key', to_row, extra)
    response.data['country_name'] = country_name(country)
    return response


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_hotels(request, country, region):
    """Top 1000 hotels of one region ("Unspecified" = hotels without a region)."""
    try:
        period, date_range = parse_period(request.query_params.get('period'))
    except InvalidPeriod as error:
        return bad_request('period', error)

    properties = (
        Property.objects.filter(country_filter(country), region_filter(region), is_deleted=False)
        .annotate(name=hotel_name_expression())
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
    extra = {'period': period, 'country': echo_key(country), 'region': echo_key(region)}
    response = ranked_page(
        request, rows, TOP_HOTELS, 'id', bookings, 'property_id',
        lambda item: {'id': item['id'], 'name': item['name'], 'city': item['city'], 'status': item['status']},
        extra,
    )
    response.data['country_name'] = country_name(country)
    response.data['region_name'] = region_name(country, region)
    return response


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
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
        year = parse_year(request.query_params.get('year'), business_today().year)
    except InvalidPeriod as error:
        return bad_request('year', error)

    prop = get_object_or_404(
        Property.objects.select_related('owner', 'country_ref')
        .annotate(region=Coalesce('region_ref__name_en', Value(UNSPECIFIED_REGION), output_field=CharField()),
                  name=hotel_name_expression()),
        pk=property_id, is_deleted=False,
    )
    owner = prop.owner
    bookings = counted_bookings().filter(property=prop)
    return Response({
        'hotel': {
            'id': prop.id, 'name': prop.name, 'status': prop.status, 'address': prop.get_full_address(),
            'city': prop.city, 'region': prop.region, 'country': prop.country,
            'country_code': prop.country_ref.code if prop.country_ref else None,
            'region_id': prop.region_ref_id, 'city_id': prop.city_ref_id,
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


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
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
    AdminAccessLog.record(request.user, 'status_users')
    return response
