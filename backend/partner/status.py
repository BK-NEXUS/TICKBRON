"""
Partner Status tabı (tek mehmanxana iyesiniń óz mehmanxanaları).

GET /api/v1/partner/status/                  akkaunt jaratılǵannan beri jıynaqlar (yamasa
    ?period= ushın, admin Status penen birdey mánisler, custom ?from=&to= de), hár
    mehmanxana boyınsha bóliw, ?granularity=day|week|month|year ushın seriya, sáykeslestiriw bloǵı hám
    ?year= ushın ayliq seriya (ádetde házirgi jıl). ?export=csv sáykeslestiriw
    kestesin júklep aladı (hár óz mehmanxanası hám oyna ushın bir qatar).
GET /api/v1/partner/status/hotels/{id}/      bir óz mehmanxana ushın sol (basqa iyeniń: 404).
GET /api/v1/partner/status/arrivals/?day=today|tomorrow   óz mehmanxanalarınıń tastıyıqlanǵan kiriwleri
    (mehmann atı, bron reference i, xona túrleri, xonalar, túnler, arnawlı sorawlar, tolıq telefon
    nomeri, e-mail joq).
Esaplanatuǵın bronlar, mehmanlar, túnler, turıwlar hám dáramat anıqlamaları: bookings/metrics.py.
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
from common.csv_export import export_response, wants_export
from common.dates import business_today
from partner.review_stats import rating_detail, ratings_by_hotel
from partner.views import IsHotelOwner
from properties.models import Property, RoomType
from properties.regions import hotel_name_expression, region_expression

RECONCILIATION_CSV_HEADER = ['hotel_id', 'hotel', 'window', 'from', 'to', 'counted_bookings', 'counted_guests',
                             'stayed_bookings', 'stayed_guests']


def bad_request(field, error):
    return Response({field: [str(error)]}, status=status.HTTP_400_BAD_REQUEST)


def own_properties(user):
    return Property.objects.filter(owner=user, is_deleted=False)


def _common(request):
    """(period, date_range, year, granularity) yamasa 400 Response."""
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


def _numbers(scope, period, date_range, year, granularity, properties):
    """Qısqasha mazmunnıń hám mehmanxana tolıq maǵlıwmatınıń ortaq bólegi, yamasa 400 Response."""
    try:
        series = metrics.series(scope, date_range, granularity)
    except InvalidPeriod as error:
        return bad_request('granularity', error)
    totals = metrics.metric_totals(scope, date_range)
    return {
        'period': period,
        'period_range': range_json(date_range),
        **metrics.status_meta(),
        'totals': totals,
        'insights': metrics.insights(scope, date_range, totals, metrics.rooms_offered(properties)),
        'granularity': granularity,
        'series': series,
        'reconciliation': metrics.reconciliation(scope),
        'months': metrics.month_comparison(scope),
        'year': year,
        'available_years': metrics.available_years(scope),
        'monthly': metrics.monthly_series(scope, year),
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
    return export_response(request, 'partner_reconciliation', RECONCILIATION_CSV_HEADER, lines())


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_status(request):
    parsed = _common(request)
    if isinstance(parsed, Response):
        return parsed
    period, date_range, year, granularity = parsed

    own = own_properties(request.user)
    if wants_export(request):
        return _reconciliation_csv(request, own)
    scope = metrics.all_bookings().filter(property__in=own)
    numbers = _numbers(scope, period, date_range, year, granularity, own)
    if isinstance(numbers, Response):
        return numbers

    rows = list(
        own.annotate(name=hotel_name_expression(), region=region_expression())
        .values('id', 'name', 'city', 'region', 'country', 'status')
        .annotate(**metrics.metric_annotations('bookings__', date_range))
        .order_by('name', 'id')
    )
    revenue = metrics.revenue_by(scope.filter(metrics.revenue_q('', date_range)), 'property_id')
    value = metrics.booking_value_by(scope.filter(metrics.counted_q('', date_range)), 'property_id')
    ratings = ratings_by_hotel([row['id'] for row in rows])
    properties = [
        {
            'id': row['id'], 'name': row['name'], 'city': row['city'], 'region': row['region'],
            'country': row['country'], 'status': row['status'],
            **metrics.grouped_row(row),
            'revenue': revenue.get(row['id'], []),
            'booking_value': value.get(row['id'], []),
            'rating': ratings[row['id']],
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
    numbers = _numbers(metrics.all_bookings().filter(property=prop), period, date_range, year, granularity,
                       Property.objects.filter(pk=prop.pk))
    if isinstance(numbers, Response):
        return numbers
    return Response({
        'hotel': {
            'id': prop.id, 'name': prop.name, 'status': prop.status, 'address': prop.get_full_address(),
            'city': prop.city, 'region': prop.region, 'country': prop.country,
        },
        'rank': metrics.region_rank(prop, date_range),
        'reviews': rating_detail(prop.id),
        **numbers,
    })


class ArrivalsPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_status_arrivals(request):
    """?day=today|tomorrow (Tashkent) kiretuǵın óz mehmanxanalarınıń tastıyıqlanǵan bronları; ?property= bir óz mehmanxana."""
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
            'phone': booking.guest_phone or '',
            'expected_arrival_time': booking.expected_arrival_time.strftime('%H:%M') if booking.expected_arrival_time else None,
            'arrived_at': booking.arrived_at.isoformat() if booking.arrived_at else None,
        }
        for booking in page
    ]
    response = paginator.get_paginated_response(results)
    response.data.update({'day': day_param, 'date': day.isoformat()})
    return response


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_status_rooms(request):
    """Iyeniń mehmanxanaları xona túrleri (?property= bir mehmanxana) ?period= degi esaplanǵan bronlar boyınsha reytingli."""
    try:
        period, date_range = period_from_request(request)
    except InvalidPeriod as error:
        return bad_request('period', error)
    own = own_properties(request.user)
    property_param = (request.query_params.get('property') or '').strip()
    if property_param:
        if not property_param.isdigit():
            return bad_request('property', 'property must be a hotel id.')
        own = own.filter(pk=get_object_or_404(own, pk=int(property_param)).pk)
    room_types = RoomType.objects.filter(property__in=own, is_deleted=False)
    names = dict(own.annotate(name=hotel_name_expression()).values_list('id', 'name'))
    rows = metrics.room_type_stats(metrics.all_bookings().filter(property__in=own), date_range, room_types)
    for row in rows:
        row['property'] = {'id': row['property_id'], 'name': names.get(row['property_id'])}
        del row['property_id']
    return Response({'period': period, 'period_range': range_json(date_range), 'rows': rows})
