"""
Admin Status bólimi: /api/v1/admin-panel/status/ (tek staff hám super-admin).

Mámleketler > regionlar > mehmanxanalar > mehmanxana tolıq maǵlıwmatı, hám mehmanlar reytingi (users), bir mehmannıń
tolıq maǵlıwmatı (R12), hám izlew, filter hám tártiplew menen tegis mehmanxanalar dizimi (R12). Mehmanxanalar
Geography ref leri boyınsha toparlanadı: mámleket ISO kodı boyınsha, region id si boyınsha, al ref i joq mehmanxanalar
URL de "unspecified" hám belgide "Unspecified" astında. Dizimler mınalardı qabıllaydı:
?period= (all, today, last_7_days, last_30_days, this_year, last_5_years, last_10_years,
?from=&to= penen custom, YYYY, YYYY-MM), ?search= (tek házirgi dizim ishinde) hám
?page= / ?page_size= (ádetde 20, eń kóbi 100). Esaplanatuǵın bronlar, mehmanlar, túnler, turıwlar
hám dáramat anıqlamaları: bookings/metrics.py.
"""
from common.alphabet import hotels_with_letter, letter_from, people_with_letter
from django.db.models import Avg, CharField, Count, DecimalField, F, Max, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Cast, Coalesce, TruncDate
from django.shortcuts import get_object_or_404
from common.dates import business_time_zone, business_today
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.models import Review
from admin_panel.models import AdminAccessLog
from admin_panel.views import IsSuperAdminOrStaff
from bookings import metrics
from bookings.metrics import InvalidPeriod, counted_q, metric_annotations, period_from_request, range_json
from common.csv_export import export_response, money_cell, wants_export
from geography.models import Country, Region
from properties.models import Property, PropertyTranslation, RoomType
from properties.regions import UNSPECIFIED_REGION, hotel_name_expression
from users.models import User

TOP_COUNTRIES = 100
TOP_REGIONS = 100
TOP_HOTELS = 1000
TOP_USERS = 1000
TOP_OVERVIEW = 5   # sholıwdaǵı eń bánt regionlar hám xona túrleri


class StatusPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


UNSPECIFIED = 'unspecified'  # Mámleket / region ref i joq mehmanxanalardıń URL bólegi hám topar kilti


def country_key(prefix=''):
    """Mehmanxana mámleketiniń topar kilti: ISO kod, yamasa UNSPECIFIED. `prefix`: Property ge jol."""
    return Coalesce(f'{prefix}country_ref__code', Value(UNSPECIFIED), output_field=CharField())


def region_key(prefix=''):
    """Mehmanxana regionınıń topar kilti: region id si tekst retinde, yamasa UNSPECIFIED."""
    return Coalesce(Cast(f'{prefix}region_ref_id', CharField()), Value(UNSPECIFIED), output_field=CharField())


def is_iso_code(value):
    return len(value) == 2 and value.isascii() and value.isalpha()


def country_q(segment, path):
    """
    URL bólegi atap kórsetken mámleket ushın Q, `path` qatnası artında ('country_ref',
    'property__country_ref'; soraw Country degi ózinde bolsa '').

    Bólek ISO kod (qálegen register) yamasa "unspecified" (mámleket joq); basqa hámme nárse hesh nárseni tańlamaydı
    (mámleket atları 2026-10-19 de kilt retinde islewdi toqtattı).
    """
    base = f'{path}__' if path else ''
    if segment.lower() == UNSPECIFIED:
        return Q(**{f'{path}__isnull': True}) if path else Q(pk__in=[])
    if is_iso_code(segment):
        return Q(**{f'{base}code': segment.upper()})
    return Q(pk__in=[])


def region_q(segment, path):
    """
    URL bólegi atap kórsetken region ushın Q, `path` artında ('region_ref'; Region degi ózinde '').

    Bólek region id si yamasa "unspecified" (region joq); basqa hámme nárse hesh nárseni tańlamaydı (region
    atları 2026-10-19 de kilt retinde islewdi toqtattı).
    """
    if segment.lower() == UNSPECIFIED:
        return Q(**{f'{path}__isnull': True}) if path else Q(pk__in=[])
    if segment.isdigit():
        return Q(**{f'{path}_id': int(segment)}) if path else Q(pk=int(segment))
    return Q(pk__in=[])


def country_filter(segment, prefix=''):
    return country_q(segment, f'{prefix}country_ref')


def region_filter(segment, prefix=''):
    return region_q(segment, f'{prefix}region_ref')


def echo_key(segment):
    """Juwapta kórsetiletuǵın kilt: kodlar úlken háriplerde, "unspecified" kishi háriplerde, qalǵanı qanday jiberilse sonday."""
    if segment.lower() == UNSPECIFIED:
        return UNSPECIFIED
    return segment.upper() if is_iso_code(segment) else segment


def names_filter(prefix, term):
    """`prefix` artındaǵı uz, ru yamasa en atında sózdi izleytuǵın Q (mısalı 'country_ref__')."""
    return (Q(**{f'{prefix}name_uz__icontains': term}) | Q(**{f'{prefix}name_ru__icontains': term})
            | Q(**{f'{prefix}name_en__icontains': term}))


def names(item, prefix):
    """Toparlanǵan qatardıń uz/ru/en atları; toparda ref joq bolsa úshewinde de "Unspecified"."""
    return {language: item[f'{prefix}name_{language}'] or UNSPECIFIED_REGION for language in ('uz', 'ru', 'en')}


def country_name(segment):
    """Belgi (breadcrumb) ushın inglizsha at; joq mámleket ushın None."""
    if segment.lower() == UNSPECIFIED:
        return UNSPECIFIED_REGION
    return Country.objects.filter(country_q(segment, '')).values_list('name_en', flat=True).first()


def region_name(country, region):
    """Mámleket ishindegi regionnıń inglizsha atı; sonday region joq bolsa None."""
    if region.lower() == UNSPECIFIED:
        return UNSPECIFIED_REGION
    return (Region.objects.filter(region_q(region, ''), country_q(country, 'country'))
            .values_list('name_en', flat=True).first())


def bad_request(field, error):
    return Response({field: [str(error)]}, status=status.HTTP_400_BAD_REQUEST)


def search_term(request):
    return (request.query_params.get('search') or '').strip()


def page_money(bookings, booking_key, keys, date_range):
    """Bir bet ushın hár kilt boyınsha dáramat hám bron mánisi (úsh jıynaqlanǵan query, bos bolsa joq)."""
    if not keys:
        return {}, {}
    on_page = bookings.filter(**{f'{booking_key}__in': keys})
    return (metrics.revenue_by(on_page.filter(metrics.revenue_q('', date_range)), booking_key),
            metrics.booking_value_by(on_page.filter(counted_q('', date_range)), booking_key))


def period_extra(period, date_range):
    return {'period': period, 'period_range': range_json(date_range), **metrics.status_meta()}


def ranked_page(request, rows, limit, key, bookings, booking_key, to_row, extra, date_range=None):
    """
    Eń joqarı `limit` toparlanǵan qatardıń bir beti, ráteli, hár valyuta boyınsha dáramat penen.

    `rows` metrics.metric_annotations() menen belgilengen tártiplengen dict ler; dáramat hám bron
    mánisi tek usı bettegi kilt ler ushın jıynaqlanadı (`bookings` = dizimge shekemlengen óshirilmegen
    Booking queryset i, `booking_key` = sol kilttiń Booking tan kórinisi).
    """
    paginator = StatusPagination()
    page = list(paginator.paginate_queryset(rows[:limit], request))
    keys = [item[key] for item in page]
    revenue, value = page_money(bookings, booking_key, keys, date_range)
    offset = (paginator.page.number - 1) * paginator.get_page_size(request)
    results = [
        {
            'rank': offset + index + 1,
            **to_row(item),
            **metrics.grouped_row(item),
            'revenue': revenue.get(item[key], []),
            'booking_value': value.get(item[key], []),
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
    """Esaplanǵan bronlar boyınsha eń jaqsı 100 mámleket: bronlar, mehmanlar, dáramat, mehmanxana sanı."""
    try:
        period, date_range = period_from_request(request)
    except InvalidPeriod as error:
        return bad_request('period', error)

    properties = Property.objects.filter(is_deleted=False).annotate(country_key=country_key())
    search = search_term(request)
    if search:
        properties = properties.filter(names_filter('country_ref__', search) | Q(country_ref__code__iexact=search))
    rows = (
        properties.values('country_key', 'country_ref__name_uz', 'country_ref__name_ru', 'country_ref__name_en')
        .annotate(hotels_count=Count('id', distinct=True),
                  **metric_annotations('bookings__', date_range))
        .order_by('-bookings_count', '-guests_count', 'country_ref__name_en', 'country_key')
    )
    bookings = metrics.all_bookings().filter(property__is_deleted=False).annotate(country_key=country_key('property__'))

    def to_row(item):
        name = names(item, 'country_ref__')
        return {
            'code': None if item['country_key'] == UNSPECIFIED else item['country_key'],
            'country': name['en'], 'name_uz': name['uz'], 'name_ru': name['ru'], 'name_en': name['en'],
            'hotels': item['hotels_count'],
        }

    return ranked_page(request, rows, TOP_COUNTRIES, 'country_key', bookings, 'country_key', to_row,
                       period_extra(period, date_range), date_range)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_regions(request, country):
    """Bir mámlekettegi eń jaqsı 100 region; regionı joq mehmanxanalar "Unspecified" retinde toparlanadı."""
    try:
        period, date_range = period_from_request(request)
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
        .annotate(hotels_count=Count('id', distinct=True),
                  **metric_annotations('bookings__', date_range))
        .order_by('-bookings_count', '-guests_count', 'region_ref__name_en', 'region_key')
    )
    bookings = (
        metrics.all_bookings()
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

    extra = {**period_extra(period, date_range), 'country': echo_key(country)}
    response = ranked_page(request, rows, TOP_REGIONS, 'region_key', bookings, 'region_key', to_row, extra,
                           date_range)
    response.data['country_name'] = country_name(country)
    return response


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_hotels(request, country, region):
    """Bir regiondaǵı eń jaqsı 1000 mehmanxana ("Unspecified" = regionı joq mehmanxanalar)."""
    try:
        period, date_range = period_from_request(request)
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
    bookings = metrics.all_bookings().filter(property__is_deleted=False)
    extra = {**period_extra(period, date_range), 'country': echo_key(country), 'region': echo_key(region)}
    response = ranked_page(
        request, rows, TOP_HOTELS, 'id', bookings, 'property_id',
        lambda item: {'id': item['id'], 'name': item['name'], 'city': item['city'], 'status': item['status']},
        extra, date_range,
    )
    response.data['country_name'] = country_name(country)
    response.data['region_name'] = region_name(country, region)
    return response


def status_scope(**filters):
    """Mehmanxanaǵa yamasa mehmanǵa shekemlengen óshirilmegen bronlar (metrics.metric_totals tiń tiykarı)."""
    return metrics.all_bookings().filter(**filters)


def granularity_from(request, default='month'):
    return metrics.parse_granularity(request.query_params.get('granularity'), default)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT, operation_id='admin_status_hotel_detail')
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_hotel_detail(request, property_id):
    """
    Bir mehmanxana: maǵlıwmat, iyeniń baylanısı, ?period= ushın jıynaqlar (booking_status penen), dáwir boyınsha
    ?granularity=day|week|month|year seriyası, sáykeslestiriw bloǵı (búgin, usı
    hápte, usı ay, usı jıl, barlıq waqıt), hám ?year= ushın ayliq seriya (ádetde
    házirgi jıl).
    """
    try:
        period, date_range = period_from_request(request)
    except InvalidPeriod as error:
        return bad_request('period', error)
    try:
        year = metrics.parse_year(request.query_params.get('year'), business_today().year)
    except InvalidPeriod as error:
        return bad_request('year', error)

    prop = get_object_or_404(
        Property.objects.select_related('owner', 'country_ref')
        .annotate(region=Coalesce('region_ref__name_en', Value(UNSPECIFIED_REGION), output_field=CharField()),
                  name=hotel_name_expression()),
        pk=property_id, is_deleted=False,
    )
    scope = status_scope(property=prop)
    try:
        granularity = granularity_from(request)
        series = metrics.series(scope, date_range, granularity)
    except InvalidPeriod as error:
        return bad_request('granularity', error)
    owner = prop.owner
    totals = metrics.metric_totals(scope, date_range)
    return Response({
        'hotel': {
            'id': prop.id, 'name': prop.name, 'status': prop.status, 'address': prop.get_full_address(),
            'city': prop.city, 'region': prop.region, 'country': prop.country,
            'country_code': prop.country_ref.code if prop.country_ref else None,
            'region_id': prop.region_ref_id,
            'registered_at': prop.created_at,
            'owner': {'id': owner.id, 'name': owner.get_full_name(), 'email': owner.email,
                      'phone': owner.phone_number},
        },
        **period_extra(period, date_range),
        'totals': totals,
        'insights': metrics.insights(scope, date_range, totals, metrics.rooms_offered(Property.objects.filter(pk=prop.pk))),
        'granularity': granularity,
        'series': series,
        'reconciliation': metrics.reconciliation(scope),
        'year': year,
        'available_years': metrics.available_years(scope),
        'monthly': metrics.monthly_series(scope, year),
    })


def _no_show_rate(totals):
    """Tólenbey qaldırılmaǵan barlıq bronlardıń no-show ı (biykar etiw dárejesi menen birdey tiykar), procent penen."""
    status = totals['booking_status']
    return metrics._percent(totals['no_show'], status['cancelled'] + totals['bookings'] + totals['no_show'])


def _new_users(first, after):
    """[first, after) aralıǵında dizimnen ótken mehmanlar (staff emes), basqa hár Status sanı sıyaqlı is kúni boyınsha."""
    day = TruncDate('date_joined', tzinfo=business_time_zone())
    return User.objects.filter(is_staff=False).annotate(day=day).filter(day__gte=first, day__lt=after).count()


def _new_user_counts(date_range, today):
    this_first = today.replace(day=1)
    last_first = metrics._previous_month(this_first)
    counts = {'current_month': _new_users(this_first, metrics._next_month(this_first)),
              'previous_month': _new_users(last_first, this_first), 'in_period': None}
    if date_range is not None:
        counts['in_period'] = _new_users(*date_range)
    return counts


def _busiest_regions(date_range):
    rows = (
        Property.objects.filter(is_deleted=False).annotate(region_key=region_key())
        .values('region_key', 'region_ref__name_uz', 'region_ref__name_ru', 'region_ref__name_en')
        .annotate(hotels_count=Count('id', distinct=True), **metric_annotations('bookings__', date_range))
        .order_by('-bookings_count', '-guests_count', 'region_ref__name_en', 'region_key')[:TOP_OVERVIEW]
    )
    result = []
    for item in rows:
        name = names(item, 'region_ref__')
        result.append({'id': None if item['region_key'] == UNSPECIFIED else int(item['region_key']),
                       'name_uz': name['uz'], 'name_ru': name['ru'], 'name_en': name['en'],
                       'hotels': item['hotels_count'], 'bookings': item['bookings_count'], 'guests': item['guests_count']})
    return result


def _busiest_room_types(scope, date_range):
    room_types = RoomType.objects.filter(is_deleted=False, property__is_deleted=False).select_related('property')
    rows = metrics.room_type_stats(scope, date_range, room_types)[:TOP_OVERVIEW]
    hotels = dict(Property.objects.filter(id__in={row['property_id'] for row in rows}).annotate(
        label=hotel_name_expression()).values_list('id', 'label'))
    return [{**row, 'property': {'id': row['property_id'], 'name': hotels.get(row['property_id'], '')}} for row in rows]


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT, operation_id='admin_status_overview')
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_overview(request):
    """
    ?period= ushın (hám ayliq grafik ushın ?year=) pútkil platforma bir qarawda: usı ay aldınǵı aymen salıstırılǵanda,
    keyingi 7 kúnde keletuǵın mehmanlar, jıynaqlar hám insight ler (biykar etiw, no-show, aldınan bronlaǵan kúnler,
    qaytıp kelgen mehmanlar), jańa mehmanlar, aktiv mehmanxanalar, eń bánt 5 region hám xona túrleri, hám jıllıq seriya.
    """
    try:
        period, date_range = period_from_request(request)
    except InvalidPeriod as error:
        return bad_request('period', error)
    try:
        year = metrics.parse_year(request.query_params.get('year'), business_today().year)
    except InvalidPeriod as error:
        return bad_request('year', error)

    today = business_today()
    scope = status_scope(property__is_deleted=False)
    totals = metrics.metric_totals(scope, date_range)
    hotels = Property.objects.filter(is_deleted=False)
    active = hotels.filter(status='active')
    return Response({
        **period_extra(period, date_range),
        'months': metrics.month_comparison(scope),
        'totals': totals,
        'insights': metrics.insights(scope, date_range, totals, metrics.rooms_offered(active)),
        'no_show_rate': _no_show_rate(totals),
        'new_users': _new_user_counts(date_range, today),
        'hotels': {'total': hotels.count(), 'active': active.count()},
        'top_regions': _busiest_regions(date_range),
        'top_room_types': _busiest_room_types(scope, date_range),
        'year': year,
        'available_years': metrics.available_years(scope),
        'monthly': metrics.monthly_series(scope, year),
    })


def _display_name(item):
    return item['full_name'] or ' '.join(filter(None, [item['first_name'], item['last_name']]))


USERS_CSV_HEADER = ['rank', 'id', 'full_name', 'phone', 'email', 'bookings', 'guests', 'nights',
                    'total_spent', 'last_booking_date']


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT, operation_id='admin_status_users_list')
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_users(request):
    """
    ?period= degi esaplanǵan bronlar boyınsha eń jaqsı 1000 mehmann: at, telefon, e-mail, bronlar, mehmanlar
    (adamlar), túnler, jámi sarıplanǵanı (juwmaqlanǵan bronlar, hár valyuta boyınsha) hám
    eń sońǵı esaplanǵan bronınıń kiriw sanası. ?search= atı/familiyası/tolıq atı, telefon, e-mail yamasa ID ge
    sáykes keledi (bólek, qálegen register). ?export=csv pútkil eń jaqsı 1000 di júklep aladı.
    """
    try:
        period, date_range = period_from_request(request)
    except InvalidPeriod as error:
        return bad_request('period', error)

    counted = counted_q('bookings__', date_range)
    users = people_with_letter(User.objects.filter(is_deleted=False), letter_from(request))
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
            guests_count=Coalesce(Sum('bookings__guest_count', filter=counted), 0),
            nights_count=Coalesce(Sum('bookings__number_of_nights', filter=counted), 0),
            last_booking_date=Max('bookings__check_in', filter=counted),
            **metrics.guest_annotations('bookings__', date_range),
        )
        .filter(bookings_count__gt=0)
        .values('id', 'full_name', 'first_name', 'last_name', 'phone_number', 'email',
                'bookings_count', 'guests_count', 'nights_count', 'last_booking_date',
                'counted_guests_count', 'stayed_guests_count', 'upcoming_guests_count')
        .order_by('-bookings_count', '-last_booking_date', 'id')
    )

    def spent_for(ids):
        if not ids:
            return {}
        return metrics.revenue_by(
            metrics.revenue_bookings(date_range).filter(guest_id__in=ids), 'guest_id')

    def to_row(rank, item, spent):
        return {
            'rank': rank,
            'id': item['id'],
            'full_name': _display_name(item),
            'first_name': item['first_name'],
            'last_name': item['last_name'],
            'phone': item['phone_number'],
            'email': item['email'],
            'bookings': item['bookings_count'],
            'guests': item['guests_count'],
            **metrics.guest_fields(item),
            'nights': item['nights_count'],
            'total_spent': spent.get(item['id'], []),
            'last_booking_date': item['last_booking_date'].isoformat(),
        }

    if wants_export(request):
        top = list(rows[:TOP_USERS])
        spent = spent_for([item['id'] for item in top])
        lines = (
            [r['rank'], r['id'], r['full_name'], r['phone'], r['email'], r['bookings'], r['guests'], r['nights'],
             money_cell(r['total_spent']), r['last_booking_date']]
            for r in (to_row(index + 1, item, spent) for index, item in enumerate(top))
        )
        return export_response(request, 'status_users', USERS_CSV_HEADER, lines)

    paginator = StatusPagination()
    page = list(paginator.paginate_queryset(rows[:TOP_USERS], request))
    spent = spent_for([item['id'] for item in page])
    offset = (paginator.page.number - 1) * paginator.get_page_size(request)
    results = [to_row(offset + index + 1, item, spent) for index, item in enumerate(page)]
    response = paginator.get_paginated_response(results)
    response.data.update(period_extra(period, date_range))
    AdminAccessLog.record(request.user, 'status_users')
    return response


HISTORY_CSV_HEADER = ['booking_id', 'reference', 'hotel_id', 'hotel', 'check_in', 'check_out', 'nights', 'rooms',
                      'guests', 'status', 'total_price', 'currency', 'charge_amount', 'charge_currency']


def _history_row(booking):
    return {
        'id': booking['id'],
        'reference': booking['confirmation_code'],
        'hotel': {'id': booking['property_id'], 'name': booking['hotel_name']},
        'check_in': booking['check_in'].isoformat(),
        'check_out': booking['check_out'].isoformat(),
        'nights': booking['number_of_nights'],
        'rooms': booking['number_of_rooms'],
        'guests': booking['guest_count'],
        'status': booking['status'],
        'total_price': f"{booking['total_price']:.2f}",
        'currency': booking['currency'],
        'charge_amount': None if booking['charge_amount'] is None else f"{booking['charge_amount']:.2f}",
        'charge_currency': booking['charge_currency'],
    }


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT, operation_id='admin_status_user_detail')
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_user_detail(request, user_id):
    """
    Bir mehmann (R12): ?period= ushın jıynaqlar (booking_status penen), barılǵan mehmanxanalar, hár mehmanxana
    boyınsha bólistiriw (bronlar, túnler, mehmanlar, hár valyutada sarıplanǵanı) hám betlerge bólingen bron
    tariyxı (hár status, eń jańa kiriw birinshi). ?export=csv tariyxtı júklep aladı.
    Audit log qa jazıladı (`status_user_view` yamasa `export_csv`).
    """
    try:
        period, date_range = period_from_request(request)
    except InvalidPeriod as error:
        return bad_request('period', error)
    user = get_object_or_404(User, pk=user_id, is_deleted=False)
    scope = status_scope(guest=user)

    history = (scope.filter(metrics.period_q('', date_range))
               .annotate(hotel_name=hotel_name_expression('property__'))
               .values('id', 'confirmation_code', 'property_id', 'hotel_name', 'check_in', 'check_out',
                       'number_of_nights', 'number_of_rooms', 'guest_count', 'status', 'total_price', 'currency',
                       'charge_amount', 'charge_currency')
               .order_by('-check_in', '-id'))

    if wants_export(request):
        def lines():
            for chunk_start in range(0, csv_limit() + 1, 500):
                chunk = list(history[chunk_start:chunk_start + 500])
                if not chunk:
                    return
                for booking in chunk:
                    r = _history_row(booking)
                    yield [r['id'], r['reference'], r['hotel']['id'], r['hotel']['name'], r['check_in'],
                           r['check_out'], r['nights'], r['rooms'], r['guests'], r['status'], r['total_price'],
                           r['currency'], r['charge_amount'], r['charge_currency']]
        return export_response(request, f'status_user_{user.id}_history', HISTORY_CSV_HEADER, lines())

    counted = scope.filter(counted_q('', date_range))
    per_hotel = list(
        counted.values('property_id')
        .annotate(bookings_count=Count('id'), guests_count=Coalesce(Sum('guest_count'), 0),
                  nights_count=Coalesce(Sum('number_of_nights'), 0),
                  stayed_count=Count('id', filter=Q(status='completed')),
                  stayed_guests_count=Coalesce(Sum('guest_count', filter=Q(status='completed')), 0),
                  last_check_in=Max('check_in'))
        .order_by('-bookings_count', '-last_check_in', 'property_id')[:TOP_HOTELS]
    )
    ids = [row['property_id'] for row in per_hotel]
    hotels = {
        row['id']: row for row in
        Property.objects.filter(id__in=ids).annotate(name=hotel_name_expression())
        .values('id', 'name', 'city', 'country')
    } if ids else {}
    spent = metrics.revenue_by(scope.filter(metrics.revenue_q('', date_range), property_id__in=ids),
                               'property_id') if ids else {}

    paginator = StatusPagination()
    page = list(paginator.paginate_queryset(history, request))
    response = paginator.get_paginated_response([_history_row(b) for b in page])
    history_data = dict(response.data)
    AdminAccessLog.record(request.user, 'status_user_view', target_user_id=user.id)
    return Response({
        'user': {
            'id': user.id, 'full_name': user.get_full_name(), 'first_name': user.first_name,
            'last_name': user.last_name, 'phone': user.phone_number, 'email': user.email,
            'date_joined': user.date_joined,
        },
        **period_extra(period, date_range),
        'totals': metrics.metric_totals(scope, date_range),
        'hotels_visited': sum(1 for row in per_hotel if row['stayed_count']),
        'hotels': [
            {
                'id': row['property_id'],
                'name': hotels.get(row['property_id'], {}).get('name'),
                'city': hotels.get(row['property_id'], {}).get('city'),
                'country': hotels.get(row['property_id'], {}).get('country'),
                'bookings': row['bookings_count'], 'stayed': row['stayed_count'],
                'nights': row['nights_count'], 'guests': row['guests_count'],
                'counted_guests': row['guests_count'], 'stayed_guests': row['stayed_guests_count'],
                'spent': spent.get(row['property_id'], []),
            }
            for row in per_hotel
        ],
        'history': history_data,
    })


def csv_limit():
    from common.csv_export import max_rows
    return max_rows()


# --- tegis mehmanxanalar dizimi (R12) ----------------------------------------------------

HOTEL_ORDERING = {
    'revenue': 'revenue_uzs', 'bookings': 'bookings_count', 'guests': 'guests_count',
    'nights': 'nights_count', 'rating': 'rating', 'created_at': 'created_at',
}
DEFAULT_HOTEL_ORDERING = '-bookings'
PROPERTY_STATUSES = {value for value, _ in Property.STATUS_CHOICES}

HOTELS_CSV_HEADER = ['rank', 'id', 'name', 'city', 'region', 'country_code', 'status', 'created_at', 'rating',
                     'bookings', 'stayed', 'guests', 'unique_customers', 'nights', 'room_nights', 'revenue',
                     'booking_value']


def parse_hotel_ordering(value):
    value = (value or DEFAULT_HOTEL_ORDERING).strip()
    field = value[1:] if value.startswith('-') else value
    if field not in HOTEL_ORDERING:
        raise InvalidPeriod(f'ordering must be one of {", ".join(sorted(HOTEL_ORDERING))} (prefix - for descending).')
    return value, HOTEL_ORDERING[field], value.startswith('-')


def uzs_revenue_by_hotel(properties, date_range):
    """{mehmanxana id: UZS dáramatı (juwmaqlanǵan bronlardıń jámi bahası)} mehmanxanalar dizimin dáramat boyınsha tártiplew
    ushın."""
    bookings = (metrics.all_bookings().filter(property__in=properties.values('id'), currency='UZS')
                .filter(metrics.revenue_q('', date_range)))
    return {row['property_id']: row['total']
            for row in bookings.values('property_id').annotate(total=Sum('total_price')).order_by()}


def _sorted_by_revenue(rows, revenue, descending):
    """Qatarlar (dict ler) UZS dáramatı boyınsha, keyin SQL tártiplewi menen birdey teń jaǵdaylar."""
    rows = sorted(rows, key=lambda item: (item['name'] or '', item['id']))
    rows.sort(key=lambda item: -item['bookings_count'])
    rows.sort(key=lambda item: revenue.get(item['id'], 0), reverse=descending)
    return rows


def rating_expression():
    rows = (Review.objects.filter(property=OuterRef('pk'), status='approved', is_deleted=False)
            .values('property').annotate(avg=Avg('overall_rating')).values('avg'))
    return Subquery(rows, output_field=DecimalField())


def hotel_search_q(term):
    in_translations = PropertyTranslation.objects.filter(name__icontains=term, is_deleted=False).values('property_id')
    return (Q(id__in=in_translations) | Q(address_line1__icontains=term) | Q(city__icontains=term)
            | names_filter('region_ref__', term)
            | names_filter('country_ref__', term) | Q(country_ref__code__iexact=term) | Q(country__icontains=term))


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT, operation_id='admin_status_hotels_list')
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def status_hotels_flat(request):
    """
    Mehmanxanalardıń tegis dizimi (R12), mámleketler > regionlar > mehmanxanalar tereńlew janında.
    ?period (+from/to), ?search= (qálegen tildegi mehmanxana atı, city, region, mámleket atı yamasa
    kodı), filter ler ?country= (ISO kod yamasa "unspecified"), ?region= (id yamasa "unspecified"),
    ?status= (property status), ?ordering= revenue|bookings|guests|nights|rating|created_at
    kemeyiw ushın "-" penen (ádetde -bookings; revenue = UZS dáramatı), eń jaqsı 1000, betlerge bólingen
    (page_size eń kóbi 100). ?export=csv pútkil eń jaqsı 1000 di júklep aladı.
    """
    try:
        period, date_range = period_from_request(request)
    except InvalidPeriod as error:
        return bad_request('period', error)
    try:
        ordering, field, descending = parse_hotel_ordering(request.query_params.get('ordering'))
    except InvalidPeriod as error:
        return bad_request('ordering', error)
    params = request.query_params
    hotel_status = (params.get('status') or '').strip()
    if hotel_status and hotel_status not in PROPERTY_STATUSES:
        return bad_request('status', f'status must be one of {", ".join(sorted(PROPERTY_STATUSES))}.')

    properties = Property.objects.filter(is_deleted=False)
    if (params.get('country') or '').strip():
        properties = properties.filter(country_filter(params['country'].strip()))
    if (params.get('region') or '').strip():
        properties = properties.filter(region_filter(params['region'].strip()))
    if hotel_status:
        properties = properties.filter(status=hotel_status)
    properties = hotels_with_letter(properties, letter_from(request))
    search = search_term(request)
    if search:
        properties = properties.filter(hotel_search_q(search))

    rows = (
        properties.annotate(name=hotel_name_expression(), rating=rating_expression())
        .values('id', 'name', 'city', 'status', 'created_at', 'rating', 'country_ref__code', 'region_ref_id',
                'region_ref__name_en')
        .annotate(**metric_annotations('bookings__', date_range))
    )
    if field == 'revenue_uzs':
        rows = _sorted_by_revenue(list(rows), uzs_revenue_by_hotel(properties, date_range), descending)
    else:
        order = F(field).desc(nulls_last=True) if descending else F(field).asc(nulls_last=True)
        rows = rows.order_by(order, '-bookings_count', 'name', 'id')
    bookings = metrics.all_bookings().filter(property__is_deleted=False)

    def to_row(item):
        return {
            'id': item['id'], 'name': item['name'], 'city': item['city'],
            'region_id': item['region_ref_id'], 'region': item['region_ref__name_en'] or UNSPECIFIED_REGION,
            'country_code': item['country_ref__code'], 'status': item['status'], 'created_at': item['created_at'],
            'rating': None if item['rating'] is None else f"{item['rating']:.2f}",
        }

    if wants_export(request):
        top = list(rows[:TOP_HOTELS])
        revenue, value = page_money(bookings, 'property_id', [item['id'] for item in top], date_range)
        lines = (
            [index + 1, item['id'], item['name'], item['city'], to_row(item)['region'], item['country_ref__code'],
             item['status'], item['created_at'].date().isoformat(), to_row(item)['rating'], item['bookings_count'],
             item['stayed_count'], item['guests_count'], item['unique_customers_count'], item['nights_count'],
             item['room_nights_count'], money_cell(revenue.get(item['id'], [])),
             money_cell(value.get(item['id'], []))]
            for index, item in enumerate(top)
        )
        return export_response(request, 'status_hotels', HOTELS_CSV_HEADER, lines)

    extra = {**period_extra(period, date_range), 'ordering': ordering}
    return ranked_page(request, rows, TOP_HOTELS, 'id', bookings, 'property_id', to_row, extra, date_range)
