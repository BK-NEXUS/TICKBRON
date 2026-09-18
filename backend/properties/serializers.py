"""
Serializers for TICKBRON property models and search results.
"""
from rest_framework import serializers
from properties.models import (
    Property, PropertyType, PropertyTranslation, PropertyPolicy,
    Amenity, AmenityCategory, PropertyAmenity, PropertyPhoto
)


class PropertyTypeSerializer(serializers.ModelSerializer):
    """Serializer for PropertyType model."""
    
    class Meta:
        model = PropertyType
        fields = ['id', 'name', 'slug', 'description', 'icon']
        read_only_fields = ['id']


class AmenityCategorySerializer(serializers.ModelSerializer):
    """Serializer for AmenityCategory model."""
    
    class Meta:
        model = AmenityCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'sort_order']
        read_only_fields = ['id']


class AmenitySerializer(serializers.ModelSerializer):
    """Serializer for Amenity model."""
    category = AmenityCategorySerializer(read_only=True)
    
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'slug', 'description', 'icon', 'is_searchable', 'sort_order', 'category']
        read_only_fields = ['id']


class PropertyAmenitySerializer(serializers.ModelSerializer):
    """Serializer for PropertyAmenity model."""
    amenity = AmenitySerializer(read_only=True)
    
    class Meta:
        model = PropertyAmenity
        fields = ['amenity', 'is_available', 'notes']
        read_only_fields = []


class PropertyPhotoSerializer(serializers.ModelSerializer):
    """Serializer for PropertyPhoto model."""
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyPhoto
        fields = ['id', 'photo', 'photo_url', 'photo_type', 'caption', 'is_primary', 'display_order', 'alt_text']
        read_only_fields = ['id']
    
    def get_photo_url(self, obj):
        """Get the absolute URL for the photo."""
        if obj.photo:
            return obj.photo.url
        return None


class PropertyTranslationSerializer(serializers.ModelSerializer):
    """Serializer for PropertyTranslation model."""
    
    class Meta:
        model = PropertyTranslation
        fields = ['language', 'name', 'description', 'address_line1', 'address_line2', 'city']
        read_only_fields = []


class PropertyPolicySerializer(serializers.ModelSerializer):
    """Serializer for PropertyPolicy model."""
    
    class Meta:
        model = PropertyPolicy
        fields = ['policy_type', 'title', 'description', 'is_strict']
        read_only_fields = []


class PropertySearchResultSerializer(serializers.ModelSerializer):
    """
    Serializer for property search results.
    
    Includes essential property information for search results display.
    """
    property_type = PropertyTypeSerializer(read_only=True)
    primary_photo = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'property_type', 'status', 'max_guests', 'bedrooms', 'bathrooms',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'latitude', 'longitude', 'base_price', 'currency', 'total_area', 'floor_number',
            'has_elevator', 'has_parking', 'has_wifi', 'has_ac', 'has_heating',
            'primary_photo', 'amenities', 'full_address', 'created_at'
        ]
        read_only_fields = ['id']
    
    def get_primary_photo(self, obj):
        """Get the primary photo for the property."""
        # Handle both model instances and serialized data
        if hasattr(obj, 'photos'):
            primary_photo = obj.photos.filter(is_primary=True, is_active=True, is_deleted=False).first()
            if primary_photo:
                return PropertyPhotoSerializer(primary_photo).data
            # Fallback to first photo if no primary
            first_photo = obj.photos.filter(is_active=True, is_deleted=False).first()
            if first_photo:
                return PropertyPhotoSerializer(first_photo).data
        return None
    
    def get_amenities(self, obj):
        """Get available amenities for the property."""
        property_amenities = obj.property_amenities.filter(
            is_available=True,
            amenity__is_searchable=True,
            is_deleted=False
        ).select_related('amenity__category')
        
        return PropertyAmenitySerializer(property_amenities, many=True).data
    
    def get_full_address(self, obj):
        """Get the full address as a string."""
        return obj.get_full_address()


class PropertyDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for property information.
    
    Includes all property details for property detail pages.
    """
    property_type = PropertyTypeSerializer(read_only=True)
    translations = PropertyTranslationSerializer(many=True, read_only=True)
    policies = PropertyPolicySerializer(many=True, read_only=True)
    photos = PropertyPhotoSerializer(many=True, read_only=True)
    amenities = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    room_types = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'owner', 'property_type', 'status', 'max_guests', 'bedrooms', 'bathrooms',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'latitude', 'longitude', 'base_price', 'currency', 'total_area', 'floor_number',
            'has_elevator', 'has_parking', 'has_wifi', 'has_ac', 'has_heating',
            'approved_at', 'approved_by', 'rejection_reason',
            'translations', 'policies', 'photos', 'amenities', 'full_address',
            'gallery', 'room_types',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'approved_at', 'approved_by', 'created_at', 'updated_at']
    
    def get_amenities(self, obj):
        """Get all amenities for the property."""
        property_amenities = obj.property_amenities.filter(
            is_deleted=False
        ).select_related('amenity__category')
        
        return PropertyAmenitySerializer(property_amenities, many=True).data
    
    def get_full_address(self, obj):
        """Get the full address as a string."""
        return obj.get_full_address()
    
    def get_gallery(self, obj):
        """Get property gallery organized by photo type."""
        photos = obj.photos.filter(
            is_active=True,
            is_deleted=False
        ).order_by('display_order', 'created_at')
        
        gallery = {
            'exterior': [],
            'interior': [],
            'amenity': [],
            'room': [],
            'other': []
        }
        
        for photo in photos:
            photo_data = PropertyPhotoSerializer(photo).data
            # Handle missing photo URL gracefully
            if not photo_data.get('photo_url'):
                photo_data['photo_url'] = None
            photo_type = photo.photo_type
            if photo_type in gallery:
                gallery[photo_type].append(photo_data)
            else:
                gallery['other'].append(photo_data)
        
        return gallery
    
    def get_room_types(self, obj):
        """Get room types with rate plans for the property."""
        from properties.models import RoomType, RatePlan
        
        room_types = obj.room_types.filter(
            is_deleted=False
        ).prefetch_related(
            'rate_plans__date_inventory',
            'photos',
            'room_amenities__amenity__category'
        )
        
        room_types_data = []
        for room_type in room_types:
            # Get active rate plans
            active_rate_plans = room_type.rate_plans.filter(
                is_active=True,
                is_deleted=False
            )
            
            rate_plans_data = []
            for rate_plan in active_rate_plans:
                rate_plan_data = {
                    'id': rate_plan.id,
                    'name': rate_plan.name,
                    'slug': rate_plan.slug,
                    'rate_type': rate_plan.rate_type,
                    'description': rate_plan.description,
                    'base_price': str(rate_plan.base_price),
                    'currency': rate_plan.currency,
                    'min_nights': rate_plan.min_nights,
                    'max_nights': rate_plan.max_nights,
                    'cancellation_policy': rate_plan.cancellation_policy,
                    'deposit_required': rate_plan.deposit_required,
                    'deposit_percentage': rate_plan.deposit_percentage,
                    'advance_booking_days': rate_plan.advance_booking_days,
                }
                rate_plans_data.append(rate_plan_data)
            
            # Get room photos
            room_photos = room_type.photos.filter(
                is_active=True,
                is_deleted=False
            ).order_by('display_order', 'created_at')
            
            room_photos_data = []
            for photo in room_photos:
                photo_data = {
                    'id': photo.id,
                    'photo': photo.photo.url if photo.photo else None,
                    'photo_type': photo.photo_type,
                    'caption': photo.caption,
                    'is_primary': photo.is_primary,
                    'display_order': photo.display_order,
                    'alt_text': photo.alt_text,
                }
                room_photos_data.append(photo_data)
            
            # Get room amenities
            room_amenities = room_type.room_amenities.filter(
                is_deleted=False
            ).select_related('amenity__category')
            
            room_amenities_data = []
            for room_amenity in room_amenities:
                amenity_data = {
                    'amenity': {
                        'id': room_amenity.amenity.id,
                        'name': room_amenity.amenity.name,
                        'slug': room_amenity.amenity.slug,
                        'description': room_amenity.amenity.description,
                        'icon': room_amenity.amenity.icon,
                        'is_searchable': room_amenity.amenity.is_searchable,
                        'category': {
                            'id': room_amenity.amenity.category.id,
                            'name': room_amenity.amenity.category.name,
                            'slug': room_amenity.amenity.category.slug,
                            'description': room_amenity.amenity.category.description,
                            'icon': room_amenity.amenity.category.icon,
                        }
                    },
                    'is_available': room_amenity.is_available,
                    'notes': room_amenity.notes,
                }
                room_amenities_data.append(amenity_data)
            
            room_type_data = {
                'id': room_type.id,
                'name': room_type.name,
                'slug': room_type.slug,
                'description': room_type.description,
                'base_occupancy': room_type.base_occupancy,
                'max_occupancy': room_type.max_occupancy,
                'base_price': str(room_type.base_price),
                'currency': room_type.currency,
                'total_rooms': room_type.total_rooms,
                'bed_configuration': room_type.bed_configuration,
                'room_size': room_type.room_size,
                'rate_plans': rate_plans_data,
                'photos': room_photos_data,
                'amenities': room_amenities_data,
            }
            room_types_data.append(room_type_data)
        
        return room_types_data


class SearchParamsSerializer(serializers.Serializer):
    """
    Serializer for search request parameters.
    
    Validates and parses search parameters for the search endpoint with standardized validation.
    """
    q = serializers.CharField(
        required=False, 
        allow_blank=True, 
        max_length=500,
        help_text="Text search query (max 500 characters)"
    )
    location = serializers.CharField(
        required=False, 
        allow_blank=True, 
        max_length=200,
        help_text="Location search (city, country, max 200 characters)"
    )
    lat = serializers.DecimalField(
        required=False, 
        max_digits=9, 
        decimal_places=6,
        min_value=-90,
        max_value=90,
        help_text="Latitude for geographic search (-90 to 90)"
    )
    lng = serializers.DecimalField(
        required=False, 
        max_digits=9, 
        decimal_places=6,
        min_value=-180,
        max_value=180,
        help_text="Longitude for geographic search (-180 to 180)"
    )
    radius = serializers.IntegerField(
        required=False, 
        default=10, 
        min_value=1, 
        max_value=100, 
        help_text="Search radius in kilometers (1-100)"
    )
    min_price = serializers.DecimalField(
        required=False, 
        max_digits=10, 
        decimal_places=2, 
        min_value=0,
        help_text="Minimum price (non-negative)"
    )
    max_price = serializers.DecimalField(
        required=False, 
        max_digits=10, 
        decimal_places=2, 
        min_value=0,
        help_text="Maximum price (non-negative)"
    )
    min_guests = serializers.IntegerField(
        required=False, 
        min_value=1, 
        max_value=50,
        help_text="Minimum number of guests (min 1)"
    )
    max_guests = serializers.IntegerField(
        required=False, 
        min_value=1, 
        max_value=50,
        help_text="Maximum number of guests (min 1)"
    )
    amenities = serializers.ListField(
        required=False,
        child=serializers.IntegerField(),
        max_length=20,
        help_text="List of amenity IDs to filter by (max 20)"
    )
    property_type = serializers.IntegerField(
        required=False, 
        min_value=1,
        help_text="Property type ID to filter by"
    )
    check_in = serializers.DateField(
        required=False, 
        help_text="Check-in date (YYYY-MM-DD format)"
    )
    check_out = serializers.DateField(
        required=False, 
        help_text="Check-out date (YYYY-MM-DD format)"
    )
    sort = serializers.ChoiceField(
        required=False,
        default='relevance',
        choices=['relevance', 'price_asc', 'price_desc', 'rating', 'distance'],
        help_text="Sorting method"
    )
    page = serializers.IntegerField(
        required=False, 
        default=1, 
        min_value=1,
        help_text="Page number (min 1)"
    )
    page_size = serializers.IntegerField(
        required=False, 
        default=20, 
        min_value=1, 
        max_value=100,
        help_text="Results per page (1-100)"
    )
    
    def validate(self, data):
        """Validate search parameters with comprehensive checks."""
        # Validate geographic search parameters
        if (data.get('lat') and not data.get('lng')) or (data.get('lng') and not data.get('lat')):
            raise serializers.ValidationError("Both lat and lng are required for geographic search")
        
        # Validate date range
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError("check_out must be after check_in")
        
        # Validate price range
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        if min_price and max_price and max_price < min_price:
            raise serializers.ValidationError("max_price must be greater than or equal to min_price")
        
        # Validate guest range
        min_guests = data.get('min_guests')
        max_guests = data.get('max_guests')
        if min_guests and max_guests and max_guests < min_guests:
            raise serializers.ValidationError("max_guests must be greater than or equal to min_guests")
        
        return data


class PaginatedSearchResponseSerializer(serializers.Serializer):
    """
    Serializer for paginated search response.
    
    Standardizes the response format for search results.
    """
    count = serializers.IntegerField(help_text="Total number of results")
    next = serializers.IntegerField(allow_null=True, help_text="Next page number")
    previous = serializers.IntegerField(allow_null=True, help_text="Previous page number")
    results = serializers.ListField(help_text="Search results")
    page = serializers.IntegerField(help_text="Current page number")
    page_size = serializers.IntegerField(help_text="Results per page")
    total_pages = serializers.IntegerField(help_text="Total number of pages")