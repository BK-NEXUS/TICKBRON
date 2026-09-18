"""
Views for TICKBRON property endpoints.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from properties.search import PropertySearchService
from properties.serializers import (
    PropertySearchResultSerializer, SearchParamsSerializer, 
    PaginatedSearchResponseSerializer
)


@api_view(['GET'])
@permission_classes([AllowAny])
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
        check_in, check_out: Date range for availability (YYYY-MM-DD format)
        sort: Sorting method (relevance, price_asc, price_desc, rating, distance)
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
        return Response(
            {'error': 'Invalid search parameters', 'details': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        # Handle unexpected errors
        return Response(
            {'error': 'Search failed', 'details': 'An unexpected error occurred during search'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Serialize results
    results_serializer = PropertySearchResultSerializer(
        search_results['results'], 
        many=True
    )
    
    response_data = {
        'count': search_results['count'],
        'next': search_results['next'],
        'previous': search_results['previous'],
        'results': results_serializer.data,
        'page': search_results.get('page', 1),
        'page_size': search_results.get('page_size', 20),
        'total_pages': search_results.get('total_pages', 1)
    }
    
    return Response(response_data, status=status.HTTP_200_OK)


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
        return Response(
            {'error': 'Failed to get suggestions', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response({'suggestions': suggestions}, status=status.HTTP_200_OK)