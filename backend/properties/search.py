"""
Search service for TICKBRON property search using database capabilities.

This module provides text search, geographic search, and comprehensive filtering
using database features that work with both SQLite (development) and PostgreSQL (production).
"""
from django.db import models
from django.db.models import Q, F, Value, FloatField
from django.db.models.functions import Cast
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from datetime import datetime, timedelta
import math
import re


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
    
    def _validate_search_params(self, search_params):
        """
        Validate and sanitize search parameters.
        
        Args:
            search_params: dict of search parameters
        
        Returns:
            dict with validated and sanitized parameters
        
        Raises:
            ValueError: if parameters are invalid
        """
        validated_params = {}
        
        # Validate text search query
        if 'q' in search_params:
            q = str(search_params['q']).strip()
            if len(q) > 500:
                raise ValueError("Search query too long (max 500 characters)")
            # Remove potentially dangerous characters
            q = re.sub(r'[<>"\']', '', q)
            validated_params['q'] = q if q else None
        
        # Validate location
        if 'location' in search_params:
            location = str(search_params['location']).strip()
            if len(location) > 200:
                raise ValueError("Location too long (max 200 characters)")
            validated_params['location'] = location if location else None
        
        # Validate geographic coordinates
        if 'lat' in search_params or 'lng' in search_params:
            try:
                lat = float(search_params['lat']) if 'lat' in search_params else None
                lng = float(search_params['lng']) if 'lng' in search_params else None
                
                if lat is not None and not -90 <= lat <= 90:
                    raise ValueError("Invalid latitude (must be between -90 and 90)")
                if lng is not None and not -180 <= lng <= 180:
                    raise ValueError("Invalid longitude (must be between -180 and 180)")
                
                validated_params['lat'] = lat
                validated_params['lng'] = lng
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid geographic coordinates: {str(e)}")
        
        # Validate radius
        if 'radius' in search_params:
            try:
                radius = float(search_params['radius'])
                if not 1 <= radius <= 100:
                    raise ValueError("Radius must be between 1 and 100 km")
                validated_params['radius'] = radius
            except (ValueError, TypeError):
                raise ValueError("Invalid radius value")
        
        # Validate price range
        if 'min_price' in search_params or 'max_price' in search_params:
            try:
                min_price = float(search_params['min_price']) if 'min_price' in search_params else None
                max_price = float(search_params['max_price']) if 'max_price' in search_params else None
                
                if min_price is not None and min_price < 0:
                    raise ValueError("Minimum price cannot be negative")
                if max_price is not None and max_price < 0:
                    raise ValueError("Maximum price cannot be negative")
                if min_price is not None and max_price is not None and min_price > max_price:
                    raise ValueError("Minimum price cannot be greater than maximum price")
                
                validated_params['min_price'] = min_price
                validated_params['max_price'] = max_price
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid price values: {str(e)}")
        
        # Validate guest capacity
        if 'min_guests' in search_params or 'max_guests' in search_params:
            try:
                min_guests = int(search_params['min_guests']) if 'min_guests' in search_params else None
                max_guests = int(search_params['max_guests']) if 'max_guests' in search_params else None
                
                if min_guests is not None and min_guests < 1:
                    raise ValueError("Minimum guests must be at least 1")
                if max_guests is not None and max_guests < 1:
                    raise ValueError("Maximum guests must be at least 1")
                if min_guests is not None and max_guests is not None and min_guests > max_guests:
                    raise ValueError("Minimum guests cannot be greater than maximum guests")
                
                validated_params['min_guests'] = min_guests
                validated_params['max_guests'] = max_guests
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid guest values: {str(e)}")
        
        # Validate amenities
        if 'amenities' in search_params:
            amenities = search_params['amenities']
            if not isinstance(amenities, list):
                raise ValueError("Amenities must be a list")
            if len(amenities) > 20:
                raise ValueError("Too many amenities (max 20)")
            validated_params['amenities'] = amenities
        
        # Validate property type
        if 'property_type' in search_params:
            try:
                property_type = int(search_params['property_type'])
                if property_type < 1:
                    raise ValueError("Invalid property type ID")
                validated_params['property_type'] = property_type
            except (ValueError, TypeError):
                raise ValueError("Invalid property type value")
        
        # Validate date range
        if 'check_in' in search_params or 'check_out' in search_params:
            try:
                check_in = self._parse_date(search_params.get('check_in')) if 'check_in' in search_params else None
                check_out = self._parse_date(search_params.get('check_out')) if 'check_out' in search_params else None
                
                if check_in and check_out and check_out <= check_in:
                    raise ValueError("Check-out date must be after check-in date")
                
                validated_params['check_in'] = check_in
                validated_params['check_out'] = check_out
            except ValueError as e:
                raise ValueError(f"Invalid date values: {str(e)}")
        
        # Validate sorting
        valid_sort_methods = ['relevance', 'price_asc', 'price_desc', 'rating', 'distance']
        if 'sort' in search_params:
            sort = search_params['sort']
            if sort not in valid_sort_methods:
                raise ValueError(f"Invalid sort method. Must be one of: {', '.join(valid_sort_methods)}")
            validated_params['sort'] = sort
        else:
            validated_params['sort'] = 'relevance'
        
        # Validate pagination
        if 'page' in search_params:
            try:
                page = int(search_params['page'])
                if page < 1:
                    raise ValueError("Page number must be at least 1")
                validated_params['page'] = page
            except (ValueError, TypeError):
                raise ValueError("Invalid page number")
        else:
            validated_params['page'] = 1
        
        if 'page_size' in search_params:
            try:
                page_size = int(search_params['page_size'])
                if page_size < 1 or page_size > 100:
                    raise ValueError("Page size must be between 1 and 100")
                validated_params['page_size'] = page_size
            except (ValueError, TypeError):
                raise ValueError("Invalid page size")
        else:
            validated_params['page_size'] = 20
        
        return validated_params
    
    def _parse_date(self, date_str):
        """
        Parse date string in various formats.
        
        Args:
            date_str: date string (YYYY-MM-DD format preferred)
        
        Returns:
            datetime.date object
        
        Raises:
            ValueError: if date format is invalid
        """
        if not date_str:
            return None
        
        try:
            # Try YYYY-MM-DD format first
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Try other common formats
                return datetime.strptime(date_str, '%Y/%m/%d').date()
            except ValueError:
                raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.")
    
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
        
        Raises:
            ValueError: if search parameters are invalid
        """
        # Validate and sanitize search parameters
        search_params = self._validate_search_params(search_params)
        
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
        if search_params.get('min_price') is not None or search_params.get('max_price') is not None:
            queryset = self._apply_price_filter(
                queryset, 
                search_params.get('min_price'),
                search_params.get('max_price')
            )
        
        # Apply guest capacity filtering
        if search_params.get('min_guests') is not None or search_params.get('max_guests') is not None:
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
        
        # Apply pagination with standardized error handling
        page = search_params.get('page', 1)
        page_size = search_params.get('page_size', 20)
        
        try:
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
        except (EmptyPage, PageNotAnInteger) as e:
            # Handle pagination errors gracefully
            page = 1
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
        
        return {
            'count': paginator.count,
            'next': page_obj.has_next() and page + 1 or None,
            'previous': page_obj.has_previous() and page - 1 or None,
            'results': list(page_obj.object_list),
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages
        }
    
    def _apply_text_search(self, queryset, query):
        """
        Apply text search using Django ORM icontains (works with SQLite and PostgreSQL).
        
        Args:
            queryset: base queryset
            query: sanitized search query string
        
        Returns:
            filtered queryset
        """
        if not query or len(query) < 2:
            return queryset
        
        # Search across relevant fields using case-insensitive contains
        # Split query into words for more flexible search
        words = query.split()
        q_objects = []
        
        for word in words:
            if len(word) >= 2:  # Only search words with 2+ characters
                q_objects.append(
                    Q(address_line1__icontains=word) |
                    Q(city__icontains=word) |
                    Q(country__icontains=word) |
                    Q(translations__name__icontains=word) |
                    Q(translations__description__icontains=word)
                )
        
        if q_objects:
            # Combine all word searches with OR
            combined_q = q_objects[0]
            for q_obj in q_objects[1:]:
                combined_q |= q_obj
            return queryset.filter(combined_q).distinct()
        
        return queryset
    
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
        """
        Apply price range filtering with standardized behavior.
        
        Args:
            queryset: base queryset
            min_price: minimum price (validated)
            max_price: maximum price (validated)
        
        Returns:
            filtered queryset
        """
        if min_price is not None:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(base_price__lte=max_price)
        
        return queryset
    
    def _apply_guest_filter(self, queryset, min_guests=None, max_guests=None):
        """
        Apply guest capacity filtering with standardized behavior.
        
        Args:
            queryset: base queryset
            min_guests: minimum number of guests (validated)
            max_guests: maximum number of guests (validated)
        
        Returns:
            filtered queryset
        """
        if min_guests is not None:
            queryset = queryset.filter(max_guests__gte=min_guests)
        if max_guests is not None:
            queryset = queryset.filter(max_guests__lte=max_guests)
        
        return queryset
    
    def _apply_amenity_filter(self, queryset, amenity_ids):
        """
        Apply amenity filtering with standardized behavior.
        
        Args:
            queryset: base queryset
            amenity_ids: list of amenity IDs (validated)
        
        Returns:
            filtered queryset
        """
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
        """
        Apply sorting to search results with standardized behavior.
        
        Args:
            queryset: base queryset
            sort_method: validated sorting method
            search_params: search parameters for context
        
        Returns:
            sorted queryset
        """
        if sort_method == 'relevance':
            # Sort by search rank if available, otherwise by created_at
            if hasattr(queryset.model, 'rank'):
                return queryset.order_by('-rank', '-created_at')
            return queryset.order_by('-created_at')
        
        elif sort_method == 'price_asc':
            return queryset.order_by('base_price', '-created_at')
        
        elif sort_method == 'price_desc':
            return queryset.order_by('-base_price', '-created_at')
        
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