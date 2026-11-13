"""
TICKBRON mehmanxana endpoint leri ushın view ler.
"""
import sys
import os
import logging
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from django.conf import settings
from common import public_cache
from currency.rates import rate_for_request, uzs_amount
from properties.search import PropertySearchService, FEATURES, SORT_OPTIONS, searchable_properties
from promotions.search import promoted_for_search, serialize_banners
from promotions.stats import IMPRESSION, record as record_stat
from properties.serializers import (
    PropertySearchResultSerializer, SearchParamsSerializer,
    PropertyDetailSerializer, PropertyAvailabilitySerializer,
    AvailabilityParamsSerializer, QuoteParamsSerializer
)
from django.utils.translation import gettext as _

# Test rejiminde isleytuǵının tekseriw
TESTING = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST')

logger = logging.getLogger('tickbron')


class SearchRateThrottle(AnonRateThrottle):
    """Izlew endpoint leri ushın rate throttle: THROTTLE_SEARCH_RATE basqasha aytpasa hár IP ge minutına 100 soraw."""
    rate = settings.SEARCH_THROTTLE_RATE
    scope = 'search'

    def allow_request(self, request, view):
        # Testler waqtında throttling di óshiriw
        if TESTING:
            return True
        return super().allow_request(request, view)


def _promoted_banners(request, search_service, search_params, page):
    """Birinshi nátiyje betiniń joqarısı ushın tólengen banner ler; reklama hesh qashan izlewdi buzbawı kerek."""
    if page != 1:
        return []
    try:
        entries = promoted_for_search(search_service, search_params)
        record_stat(IMPRESSION, [promotion.pk for promotion, _ in entries], request)
        return serialize_banners(request, entries)
    except Exception:
        logger.exception('Promoted banners failed')
        return []


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([SearchRateThrottle])
def property_search(request):
    """
    Túrli kriteriyalar boyınsha mehmanxanalardı izlew.

    Query parametrleri:
        q: Tekst izlew sorawı (eń kóbi 500 belgi)
        location: Jaylasıw izlewi (city, country, eń kóbi 200 belgi)
        lat, lng: Geografiyalıq izlew koordinatalar (lat: -90 den 90 ǵa, lng: -180 den 180 ge)
        radius: Kilometrlerde izlew radiusı (1-100, ádetde: 10)
        min_price, max_price: Baha aralıǵı (teris emes)
        min_guests, max_guests: Mehmanlar sıyımlılıǵı aralıǵı (eń kemi 1)
        amenities: Amenity ID lar dizimi (útir menen ajıratılǵan, eń kóbi 20)
        property_type: Mehmanxana túri ID si
        features: Mehmanxanada hámmesi bolıwı kerek útir menen ajıratılǵan belgiler (wifi, parking, ac, heating, elevator)
        min_rating: Tastıyıqlanǵan sharhlardıń eń kem ortasha reytingi (1-5)
        check_in, check_out: Turıwdıń hár túnine ashıq bir rate plan ı bar mehmanxanalar ǵana (YYYY-MM-DD)
        sort: Tártiplew usılı (relevance, price_asc, price_desc, rating, reviews, distance)
        page: Bet nomeri (eń kemi 1, ádetde: 1)
        page_size: Bettegi nátiyjeler (1-100, ádetde: 20)

    Qaytaradı:
        Mehmanxana maǵlıwmatı menen betlerge bólingen izlew nátiyjeleri
    """
    search_service = PropertySearchService()

    # Izlew parametrlerin oqıw hám tekseriw
    params_serializer = SearchParamsSerializer(data=request.query_params)

    if not params_serializer.is_valid():
        return Response(
            {'error': _('Invalid search parameters'), 'details': params_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    search_params = params_serializer.validated_data

    # Amenities parametrin islew (útir menen ajıratılǵan dizim)
    amenities_param = request.query_params.get('amenities')
    if amenities_param:
        try:
            search_params['amenities'] = [int(amenity_id) for amenity_id in amenities_param.split(',')]
        except (ValueError, AttributeError):
            return Response(
                {'error': _('Invalid amenities parameter format'), 'details': _('Amenities must be comma-separated integers')},
                status=status.HTTP_400_BAD_REQUEST
            )

    def find():
        search_results = search_service.search(search_params)
        results_serializer = PropertySearchResultSerializer(
            search_results['results'],
            many=True,
            context={'rate_request': request}
        )
        return {
            'count': search_results['count'],
            'next': search_results['next'],
            'previous': search_results['previous'],
            'results': results_serializer.data,
            'page': search_results.get('page', 1),
            'page_size': search_results.get('page_size', 20),
            'total_pages': search_results.get('total_pages', 1),
        }

    # Nátiyjeler hár kelwshi ushın birdey hám bir neshe sekundqa nusqalanadı; tólengen banner ler nusqanıń bólegi emes,
    # sol sebepli hár kelwshiniń olardı kóriwi ele sanaladı
    try:
        response_data = dict(public_cache.remember(request, 'search', find))
    except ValueError as e:
        # Izlew xızmetinen validation qátelikların islew
        logger.warning(f"Invalid search parameters: {e}")
        return Response(
            {'error': _('Invalid search parameters'), 'details': _('One or more search parameters are invalid.')},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception:
        # Kútilmegen qátelikterdi islew
        logger.exception('Unexpected error during property search')
        return Response(
            {'error': 'Search failed', 'details': _('An unexpected error occurred during search')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    response_data['promoted'] = _promoted_banners(request, search_service, search_params, response_data['page'])
    return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([SearchRateThrottle])
def property_filter_options(request):
    """
    Izlew jan paneli neni filterley hám tártipley aladı, izlenetuǵın mehmanxanalardan:
    eń keminde bir mehmanxanası bar mehmanxana túrleri, feature lar hám izlenetuǵın amenity ler
    mehmanxana sanları menen, baha aralıǵı hám /properties/search/ qabıllaytuǵın tártiplew usılları.
    """
    from django.db.models import Count, Max, Min, Q
    from properties.models import Amenity, PropertyType

    def build():
        properties = searchable_properties()

        property_types = PropertyType.objects.filter(is_deleted=False).annotate(
            count=Count('properties', filter=Q(properties__in=properties))
        ).filter(count__gt=0).order_by('name')

        feature_counts = properties.aggregate(**{
            feature: Count('id', filter=Q(**{flag: True})) for feature, (flag, _) in FEATURES.items()
        })

        amenities = Amenity.objects.filter(is_searchable=True, is_active=True, is_deleted=False).annotate(
            count=Count('property_amenities', filter=Q(
                property_amenities__property__in=properties,
                property_amenities__is_available=True,
                property_amenities__is_deleted=False,
            ))
        ).order_by('name')

        prices = properties.aggregate(min=Min('base_price'), max=Max('base_price'))

        return {
            'property_types': [
                {'id': t.id, 'name': t.name, 'slug': t.slug, 'count': t.count} for t in property_types
            ],
            'features': [
                {'id': feature, 'label': label, 'count': feature_counts[feature]}
                for feature, (_, label) in FEATURES.items()
            ],
            'amenities': [
                {'id': a.id, 'name': a.name, 'slug': a.slug, 'icon': a.icon, 'count': a.count} for a in amenities
            ],
            'price_range': {
                'min': float(prices['min']) if prices['min'] is not None else None,
                'max': float(prices['max']) if prices['max'] is not None else None,
            },
            'sort_options': [{'id': sort_id, 'label': label} for sort_id, label in SORT_OPTIONS],
        }

    return Response(public_cache.remember(request, 'filter-options', build), status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def property_search_suggestions(request):
    """
    Avtotolıqtırıw ushın izlew usınısların alıw.

    Query parametrleri:
        q: Bólekleyin izlew sorawı
        limit: Usınıslardıń eń kóp sanı (ádetde: 5)

    Qaytaradı:
        Izlew usınısları dizimi
    """
    search_service = PropertySearchService()

    query = request.query_params.get('q', '')
    limit = request.query_params.get('limit', 5)

    try:
        limit = int(limit)
        if limit < 1 or limit > 20:
            limit = 5
    except (ValueError, TypeError):
        limit = 5

    if not query or len(query) < 2:
        return Response({'suggestions': []}, status=status.HTTP_200_OK)

    try:
        suggestions = public_cache.remember(
            request, 'suggestions', lambda: {'suggestions': search_service.get_search_suggestions(query, limit)})['suggestions']
    except Exception:
        logger.exception('Unexpected error getting search suggestions')
        return Response(
            {'error': _('Failed to get suggestions')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({'suggestions': suggestions}, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def property_detail(request, property_id):
    """
    Tolıq bólimleri menen mehmanxananıń tolıq maǵlıwmatın alıw.

    Path parametrleri:
        property_id: Mehmanxana ID si

    Qaytaradı:
        Tolıq mehmanxana maǵlıwmatı, olardıń ishinde:
        - Tiykarǵı mehmanxana maǵlıwmatı
        - Galereya (súwretler túri boyınsha shólkemlestirilgen)
        - Kategoriyaları menen amenity ler
        - Rate plan lı xona túrleri
        - Siyasatlar
        - Awdarmalar
        - Metadata
    """
    from properties.models import Property

    def build():
        # Kútip turǵan, biykar etilgen hám toqtatılǵan mehmanxanalar ashıq emes
        property = Property.objects.get(
            id=property_id,
            status='active',
            is_active=True,
            is_deleted=False
        )
        return PropertyDetailSerializer(property, context={'rate_request': request}).data

    try:
        data = public_cache.remember(request, 'detail', build)
    except Property.DoesNotExist:
        return Response(
            {'error': 'Property not found', 'details': f'Property with ID {property_id} does not exist or is not available'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def property_availability(request, property_id):
    """
    Mehmanxananıń bos orınların hám baha aldınan qarawın alıw.

    Path parametrleri:
        property_id: Mehmanxana ID si

    Query parametrleri:
        check_in: Bos orın tekseriw ushın baslanıw sanası (YYYY-MM-DD formatı, ıqtıyarıy)
        check_out: Bos orın tekseriw ushın pitiw sanası (YYYY-MM-DD formatı, ıqtıyarıy)

    Qaytaradı:
        Mehmanxana bos orın maǵlıwmatı, olardıń ishinde:
        - Mehmanxananıń tiykarǵı maǵlıwmatı
        - Rate plan lı xona túrleri
        - Berilgen sana aralıǵı ushın bos orın hám baha menen date inventory
        - Anıq baha aldınan qarawı (birdey kirisiw = birdey shıǵıs)
    """
    from properties.models import Property

    # Sana aralıǵı parametrlerin tekseriw
    params_serializer = AvailabilityParamsSerializer(data=request.query_params)

    if not params_serializer.is_valid():
        return Response(
            {'error': _('Invalid availability parameters'), 'details': params_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    def build():
        # Kútip turǵan, biykar etilgen hám toqtatılǵan mehmanxanalar ashıq emes
        property = Property.objects.get(
            id=property_id,
            status='active',
            is_active=True,
            is_deleted=False
        )
        return PropertyAvailabilitySerializer(property, context={'request': request}).data

    try:
        # Bos xonalar bettiń qalǵanınan tezirek ózgeredi: bul nusqa jarım waqıt jasaydı
        data = public_cache.remember(request, 'availability', build, divisor=2)
    except Property.DoesNotExist:
        return Response(
            {'error': 'Property not found', 'details': f'Property with ID {property_id} does not exist or is not available'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def property_quote(request, property_id):
    """
    Bronlawdan aldın turıwdıń bahasın, onı alatuǵın kod penen esaplaw.

    Query parametrleri:
        room_type_id, rate_plan_id: xona hám baha (usı mehmanxanaǵa tiyisli bolıwı kerek)
        check_in, check_out: YYYY-MM-DD, check_out kirmeydi
        rooms: xonalar sanı (ádetde 1)

    Qaytaradı:
        { check_in, check_out, number_of_nights, number_of_rooms, currency,
          nights: [{date, price}], total_price }
        Turıwdı bronlap bolmasa 400 {error, details: {field: [message]}};
        bos orın xabarları sananı ataydı.
    """
    from django.core.exceptions import ValidationError as DjangoValidationError
    from properties.models import RatePlan
    from bookings.pricing import quote_stay, refusal_reason

    params = QuoteParamsSerializer(data=request.query_params)
    if not params.is_valid():
        return Response(
            {'error': _('Invalid quote parameters'), 'details': params.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    data = params.validated_data

    rate_plan = RatePlan.objects.filter(
        id=data['rate_plan_id'],
        room_type_id=data['room_type_id'],
        room_type__property_id=property_id,
        room_type__property__status='active',
        room_type__property__is_active=True,
        room_type__property__is_deleted=False,
        room_type__is_deleted=False,
        is_active=True,
        is_deleted=False,
    ).first()
    if rate_plan is None:
        return Response(
            {'error': _('Invalid quote parameters'),
             'details': {'rate_plan_id': [_('Rate plan not found for this room and property.')]}},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        quote = quote_stay(rate_plan, data['check_in'], data['check_out'], data['rooms'])
    except DjangoValidationError as exc:
        body = {'error': 'This stay cannot be booked', 'details': exc.message_dict}
        reason = refusal_reason(exc)
        if reason:
            body['reason'] = reason
        return Response(body, status=status.HTTP_400_BAD_REQUEST)

    def rate_of(code):
        return getattr(rate_for_request(request, code), 'rate', None)

    shown = data.get('currency') or quote.currency
    total, source = quote.total_in(shown, rate_of)
    nights = quote.nights_in(shown, rate_of)
    if total is None or nights is None:
        return Response(
            {'error': _('Exchange rate unavailable'), 'code': 'exchange_rate_unavailable',
             'details': _('No exchange rate for %(currency)s yet.') % {'currency': shown}},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    # Mehmannıń tóleytuǵını somda (Payme hám Click): bar bolsa iyeniń óz som bahası
    owner_uzs = quote.owner_prices.get('UZS') is not None and quote.currency != 'UZS'
    if owner_uzs:
        uzs = {'uzs_total': f"{quote.total_in('UZS', rate_of)[0]:.2f}", 'exchange_rate': None}
    else:
        uzs = uzs_amount(request, quote.total_price, quote.currency, 'uzs_total')
    return Response({
        'check_in': quote.check_in,
        'check_out': quote.check_out,
        'number_of_nights': quote.number_of_nights,
        'number_of_rooms': quote.number_of_rooms,
        'currency': shown,
        'price_source': source,
        'nights': [{'date': night, 'price': f'{price:.2f}'} for night, price in nights],
        'total_price': f'{total:.2f}',
        **uzs,
    }, status=status.HTTP_200_OK)
