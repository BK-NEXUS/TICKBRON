"""
Search service for TICKBRON property search using database capabilities.

This module provides text search, geographic search, and comprehensive filtering
using database features that work with both SQLite (development) and PostgreSQL (production).
"""
from django.db.models import Q, F, FloatField, Prefetch, Avg, Count, Exists, OuterRef, Subquery, IntegerField
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import date, datetime
import math
import re


# Search `features` value -> Property flag. Order is the order the sidebar shows them.
FEATURES = {
    'wifi': ('has_wifi', 'WiFi'),
    'parking': ('has_parking', 'Parking'),
    'ac': ('has_ac', 'Air Conditioning'),
    'heating': ('has_heating', 'Heating'),
    'elevator': ('has_elevator', 'Elevator'),
}

SORT_OPTIONS = [
    ('relevance', 'Relevance'),
    ('price_asc', 'Price: Low to High'),
    ('price_desc', 'Price: High to Low'),
    ('rating', 'Rating'),
    ('reviews', 'Number of Reviews'),
]


def searchable_properties():
    """Properties that search can return: approved, active and not deleted."""
    from properties.models import Property
    return Property.objects.filter(is_active=True, is_deleted=False, status='active')


def card_prices_prefetch(prefix=''):
    """
    R16: the active rate plans (with the owner's prices) a hotel card needs for its "from" price in every
    currency, as `card_room_types` on the property; `prefix` is the path to the property ("property__").
    """
    from properties.models import RatePlan, RoomType

    return Prefetch(f'{prefix}room_types', to_attr='card_room_types', queryset=RoomType.objects.filter(
        is_deleted=False).prefetch_related(Prefetch('rate_plans', queryset=RatePlan.objects.filter(
            is_active=True, is_deleted=False).prefetch_related('prices'))))


GEOGRAPHY_LEVELS = ('city_ref', 'region_ref', 'country_ref')
GEOGRAPHY_LANGUAGES = ('uz', 'ru', 'en')
MAX_SEARCH_WORDS = 8


def geography_name_filter(term):
    """Q matching the term in the uz/ru/en name of the property's city, region or country (via the refs)."""
    query = Q()
    for level in GEOGRAPHY_LEVELS:
        for language in GEOGRAPHY_LANGUAGES:
            query |= Q(**{f'{level}__name_{language}__icontains': term})
    return query


def with_review_scores(queryset):
    """
    Annotate average_rating (None without reviews) and review_count from approved reviews.
    Subqueries, so joins added by other filters cannot multiply the counts.
    """
    from accounts.models import Review

    approved = Review.objects.filter(
        property=OuterRef('pk'), status='approved', is_deleted=False,
    ).order_by().values('property')
    return queryset.annotate(
        average_rating=Subquery(
            approved.annotate(value=Avg('overall_rating')).values('value'), output_field=FloatField(),
        ),
        review_count=Coalesce(
            Subquery(approved.annotate(value=Count('id')).values('value'), output_field=IntegerField()),
            0,
        ),
    )


class PropertySearchService:
    """
    Service class for property search using PostgreSQL capabilities.
    
    Provides full-text search, geographic search, fuzzy matching, and comprehensive filtering.
    """
    
    def __init__(self):
        self.base_queryset = self._get_base_queryset()
    
    def _get_base_queryset(self):
        """Get the base queryset for property search."""
        from properties.models import PropertyAmenity, PropertyPhoto, PropertyTranslation
        
        return with_review_scores(searchable_properties()).select_related(
            'owner',
            'property_type'
        ).prefetch_related(
            # One query for every result's translations (serialized as `translations`)
            Prefetch('translations', queryset=PropertyTranslation.objects.filter(is_deleted=False)),
            # Filtered here, not in the serializer, so a result page costs the same queries for any size
            Prefetch('property_amenities', to_attr='searchable_amenities', queryset=PropertyAmenity.objects.filter(
                is_available=True, amenity__is_searchable=True, is_deleted=False).select_related('amenity__category')),
            Prefetch('photos', to_attr='active_photos', queryset=PropertyPhoto.objects.filter(
                is_active=True, is_deleted=False)),
            card_prices_prefetch(),
        )
    
    def _validate_search_params(self, search_params):
        """
        Validate and sanitize search parameters.

        Returns a dict of the cleaned parameters (defaults filled in for sort and paging).
        Raises ValueError with a message for the first parameter that is invalid.
        """
        validated_params = {}
        for check in (
            self._check_text, self._check_location, self._check_coordinates, self._check_radius,
            self._check_price_range, self._check_guest_range, self._check_amenities, self._check_property_type,
            self._check_dates, self._check_features, self._check_min_rating, self._check_sort, self._check_paging,
        ):
            check(search_params, validated_params)
        return validated_params

    @staticmethod
    def _check_text(params, out):
        if 'q' not in params:
            return
        q = str(params['q']).strip()
        if len(q) > 500:
            raise ValueError("Search query too long (max 500 characters)")
        # Remove potentially dangerous characters
        q = re.sub(r'[<>"\']', '', q)
        out['q'] = q if q else None

    @staticmethod
    def _check_location(params, out):
        if 'location' not in params:
            return
        location = str(params['location']).strip()
        if len(location) > 200:
            raise ValueError("Location too long (max 200 characters)")
        out['location'] = location if location else None

    @staticmethod
    def _optional_pair(params, low_key, high_key, convert):
        """The two ends of a range as numbers; an end that was not sent is None."""
        low = convert(params[low_key]) if low_key in params else None
        high = convert(params[high_key]) if high_key in params else None
        return low, high

    def _check_coordinates(self, params, out):
        if 'lat' not in params and 'lng' not in params:
            return
        try:
            lat, lng = self._optional_pair(params, 'lat', 'lng', float)
            if lat is not None and not -90 <= lat <= 90:
                raise ValueError("Invalid latitude (must be between -90 and 90)")
            if lng is not None and not -180 <= lng <= 180:
                raise ValueError("Invalid longitude (must be between -180 and 180)")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid geographic coordinates: {str(e)}")
        out['lat'], out['lng'] = lat, lng

    @staticmethod
    def _check_radius(params, out):
        if 'radius' not in params:
            return
        try:
            radius = float(params['radius'])
            if not 1 <= radius <= 100:
                raise ValueError("Radius must be between 1 and 100 km")
        except (ValueError, TypeError):
            raise ValueError("Invalid radius value")
        out['radius'] = radius

    def _check_price_range(self, params, out):
        if 'min_price' not in params and 'max_price' not in params:
            return
        try:
            min_price, max_price = self._optional_pair(params, 'min_price', 'max_price', float)
            if min_price is not None and min_price < 0:
                raise ValueError("Minimum price cannot be negative")
            if max_price is not None and max_price < 0:
                raise ValueError("Maximum price cannot be negative")
            if min_price is not None and max_price is not None and min_price > max_price:
                raise ValueError("Minimum price cannot be greater than maximum price")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid price values: {str(e)}")
        out['min_price'], out['max_price'] = min_price, max_price

    def _check_guest_range(self, params, out):
        if 'min_guests' not in params and 'max_guests' not in params:
            return
        try:
            min_guests, max_guests = self._optional_pair(params, 'min_guests', 'max_guests', int)
            if min_guests is not None and min_guests < 1:
                raise ValueError("Minimum guests must be at least 1")
            if max_guests is not None and max_guests < 1:
                raise ValueError("Maximum guests must be at least 1")
            if min_guests is not None and max_guests is not None and min_guests > max_guests:
                raise ValueError("Minimum guests cannot be greater than maximum guests")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid guest values: {str(e)}")
        out['min_guests'], out['max_guests'] = min_guests, max_guests

    @staticmethod
    def _check_amenities(params, out):
        if 'amenities' not in params:
            return
        amenities = params['amenities']
        if not isinstance(amenities, list):
            raise ValueError("Amenities must be a list")
        if len(amenities) > 20:
            raise ValueError("Too many amenities (max 20)")
        out['amenities'] = amenities

    @staticmethod
    def _check_property_type(params, out):
        if 'property_type' not in params:
            return
        try:
            property_type = int(params['property_type'])
            if property_type < 1:
                raise ValueError("Invalid property type ID")
        except (ValueError, TypeError):
            raise ValueError("Invalid property type value")
        out['property_type'] = property_type

    def _check_dates(self, params, out):
        if 'check_in' not in params and 'check_out' not in params:
            return
        try:
            check_in = self._parse_date(params.get('check_in')) if 'check_in' in params else None
            check_out = self._parse_date(params.get('check_out')) if 'check_out' in params else None
            if check_in and check_out and check_out <= check_in:
                raise ValueError("Check-out date must be after check-in date")
        except ValueError as e:
            raise ValueError(f"Invalid date values: {str(e)}")
        out['check_in'], out['check_out'] = check_in, check_out

    @staticmethod
    def _check_features(params, out):
        if not params.get('features'):
            return
        features = list(params['features'])
        unknown = [f for f in features if f not in FEATURES]
        if unknown:
            raise ValueError(f"Unknown features: {', '.join(unknown)}")
        out['features'] = features

    @staticmethod
    def _check_min_rating(params, out):
        if params.get('min_rating') is None:
            return
        try:
            min_rating = float(params['min_rating'])
        except (ValueError, TypeError):
            raise ValueError("Invalid minimum rating")
        if not 1 <= min_rating <= 5:
            raise ValueError("Minimum rating must be between 1 and 5")
        out['min_rating'] = min_rating

    @staticmethod
    def _check_sort(params, out):
        valid_sort_methods = [sort_id for sort_id, _ in SORT_OPTIONS] + ['distance']
        sort = params.get('sort', 'relevance')
        if sort not in valid_sort_methods:
            raise ValueError(f"Invalid sort method. Must be one of: {', '.join(valid_sort_methods)}")
        out['sort'] = sort

    @staticmethod
    def _positive_int(params, key, default, message, maximum=None):
        """An integer parameter of at least 1 (and at most `maximum`), or the default when it is not sent."""
        if key not in params:
            return default
        try:
            value = int(params[key])
            if value < 1 or (maximum is not None and value > maximum):
                raise ValueError(message)
        except (ValueError, TypeError):
            raise ValueError(message)
        return value

    def _check_paging(self, params, out):
        out['page'] = self._positive_int(params, 'page', 1, "Invalid page number")
        out['page_size'] = self._positive_int(params, 'page_size', 20, "Invalid page size", maximum=100)

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
        # SearchParamsSerializer has already turned the query value into a date
        if isinstance(date_str, date):
            return date_str
        
        try:
            # Try YYYY-MM-DD format first
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Try other common formats
                return datetime.strptime(date_str, '%Y/%m/%d').date()
            except ValueError:
                raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.")
    
    def filtered_queryset(self, search_params):
        """The searchable properties that match every filter, before sorting and paging."""
        return self._apply_filters(self.base_queryset, self._validate_search_params(search_params))

    def _apply_filters(self, queryset, search_params):
        
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
        
        # Apply feature filtering (every requested flag must be set)
        if search_params.get('features'):
            queryset = queryset.filter(**{FEATURES[f][0]: True for f in search_params['features']})
        
        # Apply minimum rating filtering (unrated properties have no rating, so they drop out)
        if search_params.get('min_rating') is not None:
            queryset = queryset.filter(average_rating__gte=search_params['min_rating'])
        
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
        
        return queryset
    
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
        
        queryset = self._apply_filters(self.base_queryset, search_params)
        
        # Apply sorting
        sort_method = search_params.get('sort', 'relevance')
        queryset = self._apply_sorting(queryset, sort_method, search_params)
        
        # Apply pagination with standardized error handling
        page = search_params.get('page', 1)
        page_size = search_params.get('page_size', 20)
        
        try:
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
        except (EmptyPage, PageNotAnInteger):
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
        
        from properties.models import PropertyTranslation

        # Each word is matched on its own, and every word must match somewhere (a word may match a
        # different field than another). With OR, "Pricey Street" matched every property on any "Street".
        # The word count is capped and translations are matched with EXISTS, so the SQL does not grow
        # with a long query (one join per word let a single anonymous request pin the database).
        for word in self._search_words(query):
            queryset = queryset.filter(
                Q(address_line1__icontains=word) |
                Q(city__icontains=word) |
                Q(country__icontains=word) |
                geography_name_filter(word) |
                Exists(PropertyTranslation.objects.filter(property=OuterRef('pk')).filter(
                    Q(name__icontains=word) | Q(description__icontains=word)))
            )
        return queryset

    @staticmethod
    def _search_words(query):
        """The first MAX_SEARCH_WORDS distinct words of 2+ characters (case-insensitive)."""
        words = []
        for word in query.split():
            if len(word) >= 2 and word.lower() not in (seen.lower() for seen in words):
                words.append(word)
        return words[:MAX_SEARCH_WORDS]

    def _apply_location_search(self, queryset, location):
        """
        Apply location-based search: names in all three languages through the Geography refs,
        plus the old text fields (the only location unmapped properties have).
        """
        return queryset.filter(
            geography_name_filter(location) |
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
        Keep properties that can be booked for the whole stay: one active rate plan
        (on an active room type) whose rate plan min/max nights allow the stay, which
        has an open DateInventory row (price/rules) for every night from check_in up to,
        not including, check_out, and whose room type has a physical room left every one
        of those nights in RoomInventory -- the shared count since 3.3 (audit #31); a
        night with no RoomInventory row is unmanaged and open at the room type's full
        total_rooms. The same rules as quote_stay.
        """
        from properties.models import DateInventory, RatePlan, RoomInventory

        check_in = self._parse_date(check_in)
        check_out = self._parse_date(check_out)
        if not check_in or not check_out or check_out <= check_in:
            return queryset
        nights = (check_out - check_in).days

        open_nights = DateInventory.objects.filter(
            rate_plan=OuterRef('pk'),
            date__gte=check_in,
            date__lt=check_out,
            is_deleted=False,
            is_available=True,
        ).filter(
            Q(minimum_stay__isnull=True) | Q(minimum_stay__lte=nights),
            Q(maximum_stay__isnull=True) | Q(maximum_stay__gte=nights),
        ).order_by().values('rate_plan').annotate(n=Count('id')).values('n')

        # Nights where the room type's shared RoomInventory row exists and is sold out
        # or closed. A missing row is unmanaged (open), so it never counts here.
        room_short_nights = RoomInventory.objects.filter(
            room_type=OuterRef('room_type'),
            date__gte=check_in,
            date__lt=check_out,
        ).filter(
            Q(is_available=False) | Q(available_rooms__lte=F('booked_rooms'))
        ).order_by().values('room_type').annotate(n=Count('id')).values('n')

        bookable_rate_plans = RatePlan.objects.filter(
            is_active=True,
            is_deleted=False,
            room_type__is_active=True,
            room_type__is_deleted=False,
            room_type__total_rooms__gt=0,
            min_nights__lte=nights,
        ).filter(
            Q(max_nights__isnull=True) | Q(max_nights__gte=nights)
        ).annotate(
            open_nights=Subquery(open_nights, output_field=IntegerField()),
            room_short_nights=Subquery(room_short_nights, output_field=IntegerField()),
        ).filter(open_nights=nights).filter(
            Q(room_short_nights__isnull=True) | Q(room_short_nights=0)
        )

        return queryset.filter(
            id__in=bookable_rate_plans.values('room_type__property_id')
        )
    
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
            # Highest average first, unrated last; more reviews wins a tie
            return queryset.order_by(
                F('average_rating').desc(nulls_last=True), '-review_count', '-created_at'
            )
        
        elif sort_method == 'reviews':
            return queryset.order_by(
                '-review_count', F('average_rating').desc(nulls_last=True), '-created_at'
            )
        
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
        
        # Places (city, region, country) that have public hotels, named in whichever language
        # matched what was typed; so the suggestion finds the same hotels when it is searched for.
        # Properties never mapped to the dictionary fall back to their text city / country.
        public = Property.objects.filter(is_active=True, is_deleted=False, status='active')
        suggestions = []

        def add(values):
            for value in values:
                if value and value not in suggestions:
                    suggestions.append(value)

        for level in GEOGRAPHY_LEVELS:
            for language in GEOGRAPHY_LANGUAGES:
                field = f'{level}__name_{language}'
                add(public.filter(**{f'{field}__icontains': query}).order_by(field)
                    .values_list(field, flat=True).distinct()[:limit])
        add(public.filter(city_ref__isnull=True, city__icontains=query)
            .order_by('city').values_list('city', flat=True).distinct()[:limit])
        add(public.filter(country_ref__isnull=True, country__icontains=query)
            .order_by('country').values_list('country', flat=True).distinct()[:limit])
        return suggestions[:limit]