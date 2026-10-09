"""
Views for TICKBRON property endpoints.
"""
import sys
import os
import logging
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from django.utils import timezone
from currency.rates import uzs_amount
from properties.search import PropertySearchService, FEATURES, SORT_OPTIONS, searchable_properties
from promotions.search import promoted_for_search
from properties.serializers import (
    PropertySearchResultSerializer, SearchParamsSerializer,
    PaginatedSearchResponseSerializer, PropertyDetailSerializer,
    PropertyAvailabilitySerializer, AvailabilityParamsSerializer, QuoteParamsSerializer
)

# Check if running in test mode
TESTING = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST')

logger = logging.getLogger('tickbron')


class SearchRateThrottle(AnonRateThrottle):
    """Rate throttle for search endpoint - 100 requests per minute per IP."""
    rate = '100/min'
    scope = 'search'

    def allow_request(self, request, view):
        # Disable throttling during tests
        if TESTING:
            return True
        return super().allow_request(request, view)


def _promoted_banners(request, search_service, search_params, page):
    """Paid banners for the top of the first results page; advertising must never break a search."""
    if page != 1:
        return []
    try:
        entries = promoted_for_search(search_service, search_params)
        items = PropertySearchResultSerializer(
            [prop for _, prop in entries], many=True, context={'rate_request': request}).data
        return [{**item, 'promotion_id': promotion.pk} for item, (promotion, _) in zip(items, entries)]
    except Exception:
        logger.exception('Promoted banners failed')
        return []


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([SearchRateThrottle])
def property_search(request):
    """
    Search for properties based on various criteria.
    
    Query Parameters:
        q: Text search query (max 500 characters)
        location: Location search (city, country, max 200 characters)
        lat, lng: Geographic search coordinates (lat: -90 to 90, lng: -180 to 180)
        radius: Search radius in kilometers (1-100, default: 10)
        min_price, max_price: Price range (non-negative)
        min_guests, max_guests: Guest capacity range (min 1)
        amenities: List of amenity IDs (comma-separated, max 20)
        property_type: Property type ID
        features: Comma-separated flags the property must all have (wifi, parking, ac, heating, elevator)
        min_rating: Minimum average rating of approved reviews (1-5)
        check_in, check_out: Only properties with one rate plan open for every night of the stay (YYYY-MM-DD)
        sort: Sorting method (relevance, price_asc, price_desc, rating, reviews, distance)
        page: Page number (min 1, default: 1)
        page_size: Results per page (1-100, default: 20)
    
    Returns:
        Paginated search results with property information
    """
    search_service = PropertySearchService()
    
    # Parse and validate search parameters
    params_serializer = SearchParamsSerializer(data=request.query_params)
    
    if not params_serializer.is_valid():
        return Response(
            {'error': 'Invalid search parameters', 'details': params_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    search_params = params_serializer.validated_data
    
    # Handle amenities parameter (comma-separated list)
    amenities_param = request.query_params.get('amenities')
    if amenities_param:
        try:
            search_params['amenities'] = [int(amenity_id) for amenity_id in amenities_param.split(',')]
        except (ValueError, AttributeError):
            return Response(
                {'error': 'Invalid amenities parameter format', 'details': 'Amenities must be comma-separated integers'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Perform search with improved error handling
    try:
        search_results = search_service.search(search_params)
    except ValueError as e:
        # Handle validation errors from search service
        logger.warning(f"Invalid search parameters: {e}")
        return Response(
            {'error': 'Invalid search parameters', 'details': 'One or more search parameters are invalid.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        # Handle unexpected errors
        logger.exception('Unexpected error during property search')
        return Response(
            {'error': 'Search failed', 'details': 'An unexpected error occurred during search'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Serialize results
    results_serializer = PropertySearchResultSerializer(
        search_results['results'],
        many=True,
        context={'rate_request': request}
    )
    
    response_data = {
        'count': search_results['count'],
        'next': search_results['next'],
        'previous': search_results['previous'],
        'results': results_serializer.data,
        'page': search_results.get('page', 1),
        'page_size': search_results.get('page_size', 20),
        'total_pages': search_results.get('total_pages', 1),
        'promoted': _promoted_banners(request, search_service, search_params, search_results.get('page', 1)),
    }
    
    return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([SearchRateThrottle])
def property_filter_options(request):
    """
    What the search sidebar can filter and sort by, from the searchable properties:
    property types that have at least one property, features and searchable amenities
    with property counts, the price range and the sort options /properties/search/ accepts.
    """
    from django.db.models import Count, Max, Min, Q
    from properties.models import Amenity, PropertyType

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

    return Response({
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
    }, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def property_search_suggestions(request):
    """
    Get search suggestions for autocomplete.
    
    Query Parameters:
        q: Partial search query
        limit: Maximum number of suggestions (default: 5)
    
    Returns:
        List of search suggestions
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
        suggestions = search_service.get_search_suggestions(query, limit)
    except Exception as e:
        logger.exception('Unexpected error getting search suggestions')
        return Response(
            {'error': 'Failed to get suggestions'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response({'suggestions': suggestions}, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def property_detail(request, property_id):
    """
    Get detailed property information with complete sections.
    
    Path Parameters:
        property_id: Property ID
    
    Returns:
        Complete property details including:
        - Basic property information
        - Gallery (photos organized by type)
        - Amenities with categories
        - Room types with rate plans
        - Policies
        - Translations
        - Metadata
    """
    from properties.models import Property
    
    try:
        # Pending, rejected and suspended properties are not public
        property = Property.objects.get(
            id=property_id,
            status='active',
            is_active=True,
            is_deleted=False
        )
    except Property.DoesNotExist:
        return Response(
            {'error': 'Property not found', 'details': f'Property with ID {property_id} does not exist or is not available'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Serialize property with all related data
    serializer = PropertyDetailSerializer(property, context={'rate_request': request})
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def property_availability(request, property_id):
    """
    Get property availability and pricing preview.
    
    Path Parameters:
        property_id: Property ID
    
    Query Parameters:
        check_in: Start date for availability check (YYYY-MM-DD format, optional)
        check_out: End date for availability check (YYYY-MM-DD format, optional)
    
    Returns:
        Property availability data including:
        - Property basic information
        - Room types with rate plans
        - Date inventory with availability and pricing for specified date range
        - Deterministic pricing preview (same inputs = same outputs)
    """
    from properties.models import Property
    
    # Validate date range parameters
    params_serializer = AvailabilityParamsSerializer(data=request.query_params)
    
    if not params_serializer.is_valid():
        return Response(
            {'error': 'Invalid availability parameters', 'details': params_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Pending, rejected and suspended properties are not public
        property = Property.objects.get(
            id=property_id,
            status='active',
            is_active=True,
            is_deleted=False
        )
    except Property.DoesNotExist:
        return Response(
            {'error': 'Property not found', 'details': f'Property with ID {property_id} does not exist or is not available'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Serialize property with availability data
    serializer = PropertyAvailabilitySerializer(
        property,
        context={'request': request}
    )

    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def property_quote(request, property_id):
    """
    Price a stay before booking, with the code that charges for it.

    Query Parameters:
        room_type_id, rate_plan_id: the room and rate (must belong to this property)
        check_in, check_out: YYYY-MM-DD, check_out exclusive
        rooms: number of rooms (default 1)

    Returns:
        { check_in, check_out, number_of_nights, number_of_rooms, currency,
          nights: [{date, price}], total_price }
        400 {error, details: {field: [message]}} when the stay cannot be booked;
        availability messages name the date.
    """
    from django.core.exceptions import ValidationError as DjangoValidationError
    from properties.models import RatePlan
    from bookings.noshow import refund_disclosure
    from bookings.pricing import quote_stay
    from django.conf import settings

    params = QuoteParamsSerializer(data=request.query_params)
    if not params.is_valid():
        return Response(
            {'error': 'Invalid quote parameters', 'details': params.errors},
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
            {'error': 'Invalid quote parameters',
             'details': {'rate_plan_id': ['Rate plan not found for this room and property.']}},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        quote = quote_stay(rate_plan, data['check_in'], data['check_out'], data['rooms'])
    except DjangoValidationError as exc:
        return Response(
            {'error': 'This stay cannot be booked', 'details': exc.message_dict},
            status=status.HTTP_400_BAD_REQUEST
        )

    uzs = uzs_amount(request, quote.total_price, quote.currency, 'uzs_total')
    return Response({
        'check_in': quote.check_in,
        'check_out': quote.check_out,
        'number_of_nights': quote.number_of_nights,
        'number_of_rooms': quote.number_of_rooms,
        'currency': quote.currency,
        'nights': [{'date': night, 'price': f'{price:.2f}'} for night, price in quote.nights],
        'total_price': f'{quote.total_price:.2f}',
        **uzs,
        # R12: what the guest is told before paying (the booking stores this percent at creation)
        **refund_disclosure(settings.NO_SHOW_REFUND_PERCENT, uzs['uzs_total']),
    }, status=status.HTTP_200_OK)