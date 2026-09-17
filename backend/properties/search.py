"""
Search service for TICKBRON property search using database capabilities.

This module provides text search, geographic search, and comprehensive filtering
using database features that work with both SQLite (development) and PostgreSQL (production).
"""
from django.db import models
from django.db.models import Q, F, Value, FloatField
from django.db.models.functions import Cast
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import math


class PropertySearchService:
    """
    Service class for property search using PostgreSQL capabilities.
    
    Provides full-text search, geographic search, fuzzy matching, and comprehensive filtering.
    """
    
    def __init__(self):
        self.base_queryset = self._get_base_queryset()
    
    def _get_base_queryset(self):
        """Get the base queryset for property search."""
        from properties.models import Property
        
        return Property.objects.filter(
            is_active=True,
            is_deleted=False,
            status='active'
        ).select_related(
            'owner',
            'property_type'
        ).prefetch_related(
            'translations',
            'property_amenities__amenity',
            'photos'
        )
    
    def search(self, search_params):
        """
        Perform property search based on provided parameters.
        
        Args:
            search_params: dict containing search parameters
                - q: text search query
                - location: location search (city, country)
                - lat, lng, radius: geographic search
                - min_price, max_price: price range
                - min_guests, max_guests: guest capacity
                - amenities: list of amenity IDs
                - property_type: property type ID
                - check_in, check_out: date range for availability
                - sort: sorting method (relevance, price_asc, price_desc, rating, distance)
                - page: page number
                - page_size: results per page
        
        Returns:
            dict with search results and metadata
        """
        queryset = self.base_queryset
        
        # Apply text search
        if search_params.get('q'):
            queryset = self._apply_text_search(queryset, search_params['q'])
        
        # Apply location search
        if search_params.get('location'):
            queryset = self._apply_location_search(queryset, search_params['location'])
        
        # Apply geographic search
        if all(k in search_params for k in ['lat', 'lng']):
            radius = search_params.get('radius', 10)  # default 10km
            queryset = self._apply_geographic_search(
                queryset, 
                search_params['lat'], 
                search_params['lng'], 
                radius
            )
        
        # Apply price filtering
        if search_params.get('min_price') or search_params.get('max_price'):
            queryset = self._apply_price_filter(
                queryset, 
                search_params.get('min_price'),
                search_params.get('max_price')
            )
        
        # Apply guest capacity filtering
        if search_params.get('min_guests') or search_params.get('max_guests'):
            queryset = self._apply_guest_filter(
                queryset,
                search_params.get('min_guests'),
                search_params.get('max_guests')
            )
        
        # Apply amenity filtering
        if search_params.get('amenities'):
            queryset = self._apply_amenity_filter(queryset, search_params['amenities'])
        
        # Apply property type filtering
        if search_params.get('property_type'):
            queryset = self._apply_property_type_filter(queryset, search_params['property_type'])
        
        # Apply date availability filtering
        if search_params.get('check_in') and search_params.get('check_out'):
            queryset = self._apply_date_filter(
                queryset,
                search_params['check_in'],
                search_params['check_out']
            )
        
        # Apply sorting
        sort_method = search_params.get('sort', 'relevance')
        queryset = self._apply_sorting(queryset, sort_method, search_params)
        
        # Apply pagination
        page = search_params.get('page', 1)
        page_size = search_params.get('page_size', 20)
        
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'count': paginator.count,
            'next': page_obj.has_next() and page + 1 or None,
            'previous': page_obj.has_previous() and page - 1 or None,
            'results': list(page_obj.object_list)
        }
    
    def _apply_text_search(self, queryset, query):
        """Apply text search using Django ORM icontains (works with SQLite and PostgreSQL)."""
        # Search across relevant fields using case-insensitive contains
        return queryset.filter(
            Q(address_line1__icontains=query) |
            Q(city__icontains=query) |
            Q(country__icontains=query) |
            Q(translations__name__icontains=query) |
            Q(translations__description__icontains=query)
        ).distinct()
    
    def _apply_location_search(self, queryset, location):
        """Apply location-based search (city, country)."""
        return queryset.filter(
            Q(city__icontains=location) |
            Q(country__icontains=location) |
            Q(address_line1__icontains=location)
        )
    
    def _apply_geographic_search(self, queryset, lat, lng, radius_km):
        """
        Apply geographic search using simplified bounding box approach.
        
        Args:
            queryset: base queryset
            lat: latitude of search center
            lng: longitude of search center
            radius_km: search radius in kilometers
        """
        # Simple bounding box approach for cross-database compatibility
        # Convert radius to approximate degrees (1 degree ≈ 111 km)
        lat_range = radius_km / 111.0
        lng_range = radius_km / (111.0 * math.cos(math.radians(float(lat))))
        
        return queryset.filter(
            latitude__gte=float(lat) - lat_range,
            latitude__lte=float(lat) + lat_range,
            longitude__gte=float(lng) - lng_range,
            longitude__lte=float(lng) + lng_range
        )
    
    def _apply_price_filter(self, queryset, min_price=None, max_price=None):
        """Apply price range filtering."""
        if min_price is not None:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(base_price__lte=max_price)
        
        return queryset
    
    def _apply_guest_filter(self, queryset, min_guests=None, max_guests=None):
        """Apply guest capacity filtering."""
        if min_guests is not None:
            queryset = queryset.filter(max_guests__gte=min_guests)
        if max_guests is not None:
            queryset = queryset.filter(max_guests__lte=max_guests)
        
        return queryset
    
    def _apply_amenity_filter(self, queryset, amenity_ids):
        """Apply amenity filtering."""
        from properties.models import PropertyAmenity
        
        # Filter properties that have all specified amenities
        for amenity_id in amenity_ids:
            queryset = queryset.filter(
                property_amenities__amenity_id=amenity_id,
                property_amenities__is_available=True
            )
        
        return queryset.distinct()
    
    def _apply_property_type_filter(self, queryset, property_type_id):
        """Apply property type filtering."""
        return queryset.filter(property_type_id=property_type_id)
    
    def _apply_date_filter(self, queryset, check_in, check_out):
        """
        Apply date availability filtering.
        
        This checks if properties have availability for the requested date range.
        For now, this is a basic implementation - can be enhanced with inventory integration.
        """
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            # Invalid date format, skip filtering
            return queryset
        
        # Ensure check_out is after check_in
        if check_out_date <= check_in_date:
            return queryset
        
        # Basic availability check - ensure property exists and is active
        # More sophisticated inventory checking can be added in future checkpoints
        return queryset
    
    def _apply_sorting(self, queryset, sort_method, search_params):
        """Apply sorting to search results."""
        if sort_method == 'relevance':
            # Sort by search rank if available, otherwise by created_at
            if hasattr(queryset.model, 'rank'):
                return queryset.order_by('-rank', '-created_at')
            return queryset.order_by('-created_at')
        
        elif sort_method == 'price_asc':
            return queryset.order_by('base_price')
        
        elif sort_method == 'price_desc':
            return queryset.order_by('-base_price')
        
        elif sort_method == 'rating':
            # For now, sort by created_at as rating field will be added later
            return queryset.order_by('-created_at')
        
        elif sort_method == 'distance':
            # Sort by distance from search center (simplified approach)
            # For now, sort by created_at as proper distance sorting requires complex calculation
            return queryset.order_by('-created_at')
        
        # Default sorting
        return queryset.order_by('-created_at')
    
    def get_search_suggestions(self, query, limit=5):
        """
        Get search suggestions for autocomplete.
        
        Args:
            query: partial search query
            limit: maximum number of suggestions
        
        Returns:
            list of suggestion strings
        """
        from properties.models import Property
        
        if not query or len(query) < 2:
            return []
        
        # Get matching cities and countries
        cities = Property.objects.filter(
            is_active=True,
            is_deleted=False,
            city__icontains=query
        ).values_list('city', flat=True).distinct()[:limit]
        
        countries = Property.objects.filter(
            is_active=True,
            is_deleted=False,
            country__icontains=query
        ).values_list('country', flat=True).distinct()[:limit]
        
        suggestions = list(set(list(cities) + list(countries)))
        return suggestions[:limit]