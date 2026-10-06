"""
Partner Status tab (the hotel owner's own properties only).

GET /api/v1/partner/status/                  totals since the account was created (or for
    ?period=, same values as the admin Status incl. custom ?from=&to=), a per-property
    breakdown, a series for ?granularity=day|week|month|year, the reconciliation block and the
    monthly series for ?year= (default: the current year). ?export=csv downloads the
    reconciliation table (one row per own hotel and window).
GET /api/v1/partner/status/hotels/{id}/      the same for one own hotel (another owner's: 404).
GET /api/v1/partner/status/arrivals/?day=today|tomorrow   confirmed check-ins of own hotels
    (guest name, booking reference, room types, rooms, nights, special requests, phone last 4
    digits only, no email).
Definitions of counted bookings, guests, nights, stays and revenue: bookings/metrics.py.
"""
from datetime import timedelta

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from bookings import metrics
from bookings.metrics import InvalidPeriod, period_from_request, range_json
from bookings.models import Booking, BookingItem
from common.csv_export import csv_response, wants_csv
from common.dates import business_today
from partner.views import IsHotelOwner
from properties.models import Property
from properties.regions import hotel_name_expression, region_expression

RECONCILIATION_CSV_HEADER = ['hotel_id', 'hotel', 'window', 'from', 'to', 'counted_bookings', 'counted_guests',
                             'stayed_bookings', 'stayed_guests']


def bad_request(field, error):
    return Response({field: [str(error)]}, status=status.HTTP_400_BAD_REQUEST)


def refunded_ids(date_range, own=None):
    """Fully refunded booking ids in the period (see metrics.fully_refunded_ids)."""
    scope = metrics.all_bookings().filter(metrics.period_q('', date_range))
    return metrics.fully_refunded_ids(scope if own is None else scope.filter(property__in=own))


def own_properties(user):
    return Property.objects.filter(owner=user, is_deleted=False)


def _common(request):
    """(period, date_range, year, granularity) or a 400 Response."""
    try:
        period, date_range = period_from_request(request)
    except InvalidPeriod as error:
        return bad_request('period', error)
    try:
        year = metrics.parse_year(request.query_params.get('year'), business_today().year)
    except InvalidPeriod as error:
        return bad_request('year', error)
    try:
        granularity = metrics.parse_granularity(request.query_params.get('granularity'))
    except InvalidPeriod as error:
        return bad_request('granularity', error)
    return period, date_range, year, granularity


def _numbers(scope, period, date_range, year, granularity):
    """The shared part of the summary and the hotel detail, or a 400 Response."""
    refunded = metrics.fully_refunded_ids(scope)
    try:
        series = metrics.series(scope, date_range, granularity, refunded_ids=refunded)
    except InvalidPeriod as error:
        return bad_request('granularity', error)
    return {
        'period': period,
        'period_range': range_json(date_range),
        'totals': metrics.metric_totals(scope, date_range, refunded_ids=refunded),
        'granularity': granularity,
        'series': series,
        'reconciliation': metrics.reconciliation(scope, refunded_ids=refunded),
        'year': year,
        'available_years': metrics.available_years(scope, refunded),
        'monthly': metrics.monthly_series(scope, year, refunded),
    }


def _reconciliation_csv(request, own):
    names = dict(own.annotate(name=hotel_name_expression()).values_list('id', 'name'))
    blocks = metrics.reconciliation_by(metrics.all_bookings().filter(property__in=own), 'property_id')
    empty = metrics.reconciliation(metrics.all_bookings().none())

    def lines():
        for hotel_id in sorted(names, key=lambda pk: (names[pk] or '', pk)):
            for window, row in blocks.get(hotel_id, empty).items():
                yield [hotel_id, names[hotel_id], window, row['from'], row['to'], row['counted']['bookings'],
                       row['counted']['guests'], row['stayed']['bookings'], row['stayed']['guests']]
    return csv_response(request, 'partner_reconciliation', RECONCILIATION_CSV_HEADER, lines())


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_status(request):
    parsed = _common(request)
    if isinstance(parsed, Response):
        return parsed
    period, date_range, year, granularity = parsed

    own = own_properties(request.user)
    if wants_csv(request):
        return _reconciliation_csv(request, own)
    scope = metrics.all_bookings().filter(property__in=own)
    numbers = _numbers(scope, period, date_range, year, granularity)
    if isinstance(numbers, Response):
        return numbers

    rows = list(
        own.annotate(name=hotel_name_expression(), region=region_expression())
        .values('id', 'name', 'city', 'region', 'country', 'status')
        .annotate(**metrics.metric_annotations('bookings__', date_range, refunded_ids(date_range, own)))
        .order_by('name', 'id')
    )
    revenue = metrics.revenue_by(scope.filter(metrics.revenue_q('', date_range)), 'property_id')
    value = metrics.booking_value_by(scope.filter(metrics.counted_q('', date_range)), 'property_id')
    properties = [
        {
            'id': row['id'], 'name': row['name'], 'city': row['city'], 'region': row['region'],
            'country': row['country'], 'status': row['status'],
            **metrics.grouped_row(row),
            'revenue': revenue.get(row['id'], []),
            'booking_value': value.get(row['id'], []),
        }
        for row in rows
    ]
    return Response({
        'since': request.user.date_joined.date().isoformat(),
        **numbers,
        'properties': properties,
    })


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_status_hotel(request, property_id):
    parsed = _common(request)
    if isinstance(parsed, Response):
        return parsed
    period, date_range, year, granularity = parsed
    prop = get_object_or_404(
        own_properties(request.user).annotate(name=hotel_name_expression(), region=region_expression()),
        pk=property_id,
    )
    numbers = _numbers(metrics.all_bookings().filter(property=prop), period, date_range, year, granularity)
    if isinstance(numbers, Response):
        return numbers
    return Response({
        'hotel': {
            'id': prop.id, 'name': prop.name, 'status': prop.status, 'address': prop.get_full_address(),
            'city': prop.city, 'region': prop.region, 'country': prop.country,
        },
        **numbers,
    })


class ArrivalsPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


def phone_last4(phone):
    digits = ''.join(ch for ch in (phone or '') if ch.isdigit())
    return digits[-4:] if digits else None


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_status_arrivals(request):
    """Confirmed bookings of own hotels checking in ?day=today|tomorrow (Tashkent); ?property= one own hotel."""
    day_param = (request.query_params.get('day') or 'today').strip()
    if day_param not in ('today', 'tomorrow'):
        return bad_request('day', 'day must be "today" or "tomorrow".')
    day = business_today() + timedelta(days=1 if day_param == 'tomorrow' else 0)

    own = own_properties(request.user)
    property_param = (request.query_params.get('property') or '').strip()
    if property_param:
        if not property_param.isdigit():
            return bad_request('property', 'property must be a hotel id.')
        hotel = get_object_or_404(own, pk=int(property_param))
        own = own.filter(pk=hotel.pk)

    bookings = (
        Booking.objects.filter(property__in=own, is_deleted=False, status='confirmed', check_in=day)
        .annotate(hotel_name=hotel_name_expression('property__'))
        .prefetch_related(Prefetch('booking_items', queryset=BookingItem.objects.select_related('room_type')
                                   .filter(is_deleted=False).order_by('id')))
        .order_by('hotel_name', 'property_id', 'id')
    )
    paginator = ArrivalsPagination()
    page = paginator.paginate_queryset(bookings, request)
    results = [
        {
            'id': booking.id,
            'reference': booking.confirmation_code,
            'property': {'id': booking.property_id, 'name': booking.hotel_name},
            'guest_name': booking.guest_full_name,
            'room_types': [item.room_type.name for item in booking.booking_items.all()],
            'rooms': booking.number_of_rooms,
            'nights': booking.number_of_nights,
            'guests': booking.guest_count,
            'check_in': booking.check_in.isoformat(),
            'check_out': booking.check_out.isoformat(),
            'special_requests': booking.special_requests or '',
            'phone_last4': phone_last4(booking.guest_phone),
        }
        for booking in page
    ]
    response = paginator.get_paginated_response(results)
    response.data.update({'day': day_param, 'date': day.isoformat()})
    return response
