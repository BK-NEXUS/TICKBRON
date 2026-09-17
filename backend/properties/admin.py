"""
Admin configuration for property models.
"""
from django.contrib import admin
from properties.models import (
    PropertyType, Property, PropertyTranslation, PropertyPolicy,
    AmenityCategory, AmenityCategoryTranslation, Amenity, AmenityTranslation, PropertyAmenity,
    PropertyPhoto, RoomType, RoomPhoto, RoomAmenity, RatePlan, DateInventory
)


@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    """
    Admin interface for PropertyType model.
    """
    list_display = ('name', 'slug', 'description', 'icon', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


class PropertyTranslationInline(admin.TabularInline):
    """
    Inline admin for PropertyTranslation.
    """
    model = PropertyTranslation
    extra = 0
    fields = ('language', 'name', 'description', 'address_line1', 'city')


class PropertyPolicyInline(admin.TabularInline):
    """
    Inline admin for PropertyPolicy.
    """
    model = PropertyPolicy
    extra = 0
    fields = ('policy_type', 'title', 'description', 'is_strict')


class PropertyAmenityInline(admin.TabularInline):
    """
    Inline admin for PropertyAmenity.
    """
    model = PropertyAmenity
    extra = 0
    fields = ('amenity', 'is_available', 'notes')
    autocomplete_fields = ['amenity']


class PropertyPhotoInline(admin.TabularInline):
    """
    Inline admin for PropertyPhoto.
    """
    model = PropertyPhoto
    extra = 0
    fields = ('photo', 'photo_type', 'caption', 'is_primary', 'display_order', 'alt_text')
    readonly_fields = ('created_at',)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """
    Admin interface for Property model.
    """
    list_display = ('id', 'owner', 'property_type', 'status', 'city', 'country', 'base_price', 'currency', 'max_guests', 'is_active', 'created_at')
    list_filter = ('status', 'property_type', 'country', 'currency', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('owner__email', 'city', 'country', 'address_line1')
    ordering = ('-created_at',)
    inlines = [PropertyTranslationInline, PropertyPolicyInline, PropertyAmenityInline, PropertyPhotoInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'property_type', 'status')
        }),
        ('Capacity', {
            'fields': ('max_guests', 'bedrooms', 'bathrooms')
        }),
        ('Location', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'latitude', 'longitude')
        }),
        ('Pricing', {
            'fields': ('base_price', 'currency')
        }),
        ('Additional Info', {
            'fields': ('total_area', 'floor_number', 'has_elevator', 'has_parking', 'has_wifi', 'has_ac', 'has_heating')
        }),
        ('Approval', {
            'fields': ('approved_at', 'approved_by', 'rejection_reason')
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted', 'deleted_at')
        }),
    )


@admin.register(PropertyTranslation)
class PropertyTranslationAdmin(admin.ModelAdmin):
    """
    Admin interface for PropertyTranslation model.
    """
    list_display = ('property', 'language', 'name', 'city', 'created_at')
    list_filter = ('language', 'created_at')
    search_fields = ('name', 'description', 'property__id')
    ordering = ('property', 'language')


@admin.register(PropertyPolicy)
class PropertyPolicyAdmin(admin.ModelAdmin):
    """
    Admin interface for PropertyPolicy model.
    """
    list_display = ('property', 'policy_type', 'title', 'is_strict', 'created_at')
    list_filter = ('policy_type', 'is_strict', 'created_at')
    search_fields = ('title', 'description', 'property__id')
    ordering = ('property', 'policy_type')


class AmenityCategoryTranslationInline(admin.TabularInline):
    """
    Inline admin for AmenityCategoryTranslation.
    """
    model = AmenityCategoryTranslation
    extra = 0
    fields = ('language', 'name', 'description')


@admin.register(AmenityCategory)
class AmenityCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for AmenityCategory model.
    """
    list_display = ('name', 'slug', 'description', 'icon', 'sort_order', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('sort_order', 'name')
    inlines = [AmenityCategoryTranslationInline]


@admin.register(AmenityCategoryTranslation)
class AmenityCategoryTranslationAdmin(admin.ModelAdmin):
    """
    Admin interface for AmenityCategoryTranslation model.
    """
    list_display = ('category', 'language', 'name', 'created_at')
    list_filter = ('language', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    ordering = ('category', 'language')


class AmenityTranslationInline(admin.TabularInline):
    """
    Inline admin for AmenityTranslation.
    """
    model = AmenityTranslation
    extra = 0
    fields = ('language', 'name', 'description')


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    """
    Admin interface for Amenity model.
    """
    list_display = ('name', 'slug', 'category', 'description', 'icon', 'is_searchable', 'sort_order', 'is_active', 'created_at')
    list_filter = ('category', 'is_searchable', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('category', 'sort_order', 'name')
    autocomplete_fields = ['category']
    inlines = [AmenityTranslationInline]


@admin.register(AmenityTranslation)
class AmenityTranslationAdmin(admin.ModelAdmin):
    """
    Admin interface for AmenityTranslation model.
    """
    list_display = ('amenity', 'language', 'name', 'created_at')
    list_filter = ('language', 'created_at')
    search_fields = ('name', 'description', 'amenity__name')
    ordering = ('amenity', 'language')


@admin.register(PropertyAmenity)
class PropertyAmenityAdmin(admin.ModelAdmin):
    """
    Admin interface for PropertyAmenity model.
    """
    list_display = ('property', 'amenity', 'is_available', 'created_at')
    list_filter = ('is_available', 'amenity__category', 'created_at')
    search_fields = ('property__id', 'amenity__name', 'notes')
    ordering = ('property', 'amenity')
    raw_id_fields = ('property', 'amenity')


@admin.register(PropertyPhoto)
class PropertyPhotoAdmin(admin.ModelAdmin):
    """
    Admin interface for PropertyPhoto model.
    """
    list_display = ('property', 'photo_type', 'caption', 'is_primary', 'display_order', 'created_at')
    list_filter = ('photo_type', 'is_primary', 'created_at')
    search_fields = ('property__id', 'caption', 'alt_text')
    ordering = ('property', 'display_order', 'created_at')
    raw_id_fields = ('property',)
    
    fieldsets = (
        ('Photo Information', {
            'fields': ('property', 'photo', 'photo_type')
        }),
        ('Display Settings', {
            'fields': ('caption', 'is_primary', 'display_order', 'alt_text')
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted', 'deleted_at')
        }),
    )


class RoomPhotoInline(admin.TabularInline):
    """
    Inline admin for RoomPhoto.
    """
    model = RoomPhoto
    extra = 0
    fields = ('photo', 'photo_type', 'caption', 'is_primary', 'display_order', 'alt_text')
    readonly_fields = ('created_at',)


class RoomAmenityInline(admin.TabularInline):
    """
    Inline admin for RoomAmenity.
    """
    model = RoomAmenity
    extra = 0
    fields = ('amenity', 'is_available', 'notes')
    autocomplete_fields = ['amenity']


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    """
    Admin interface for RoomType model.
    """
    list_display = ('property', 'name', 'slug', 'base_occupancy', 'max_occupancy', 'base_price', 'currency', 'total_rooms', 'is_active', 'created_at')
    list_filter = ('property', 'currency', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description', 'property__id')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('property', 'name')
    inlines = [RoomPhotoInline, RoomAmenityInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('property', 'name', 'slug', 'description')
        }),
        ('Capacity', {
            'fields': ('base_occupancy', 'max_occupancy', 'total_rooms')
        }),
        ('Pricing', {
            'fields': ('base_price', 'currency')
        }),
        ('Room Details', {
            'fields': ('bed_configuration', 'room_size')
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted', 'deleted_at')
        }),
    )


@admin.register(RoomPhoto)
class RoomPhotoAdmin(admin.ModelAdmin):
    """
    Admin interface for RoomPhoto model.
    """
    list_display = ('room_type', 'photo_type', 'caption', 'is_primary', 'display_order', 'created_at')
    list_filter = ('photo_type', 'is_primary', 'created_at')
    search_fields = ('room_type__name', 'caption', 'alt_text')
    ordering = ('room_type', 'display_order', 'created_at')
    raw_id_fields = ('room_type',)
    
    fieldsets = (
        ('Photo Information', {
            'fields': ('room_type', 'photo', 'photo_type')
        }),
        ('Display Settings', {
            'fields': ('caption', 'is_primary', 'display_order', 'alt_text')
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted', 'deleted_at')
        }),
    )


@admin.register(RoomAmenity)
class RoomAmenityAdmin(admin.ModelAdmin):
    """
    Admin interface for RoomAmenity model.
    """
    list_display = ('room_type', 'amenity', 'is_available', 'created_at')
    list_filter = ('is_available', 'amenity__category', 'created_at')
    search_fields = ('room_type__name', 'amenity__name', 'notes')
    ordering = ('room_type', 'amenity')
    raw_id_fields = ('room_type', 'amenity')


@admin.register(RatePlan)
class RatePlanAdmin(admin.ModelAdmin):
    """
    Admin interface for RatePlan model.
    """
    list_display = ('room_type', 'name', 'slug', 'rate_type', 'base_price', 'currency', 'min_nights', 'max_nights', 'is_active', 'created_at')
    list_filter = ('rate_type', 'currency', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description', 'room_type__name')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('room_type', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('room_type', 'name', 'slug', 'rate_type', 'description')
        }),
        ('Pricing', {
            'fields': ('base_price', 'currency')
        }),
        ('Booking Rules', {
            'fields': ('min_nights', 'max_nights', 'advance_booking_days')
        }),
        ('Policies', {
            'fields': ('cancellation_policy', 'deposit_required', 'deposit_percentage')
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted', 'deleted_at')
        }),
    )


@admin.register(DateInventory)
class DateInventoryAdmin(admin.ModelAdmin):
    """
    Admin interface for DateInventory model.
    """
    list_display = ('rate_plan', 'date', 'available_rooms', 'booked_rooms', 'get_remaining_rooms', 'price', 'currency', 'is_available', 'created_at')
    list_filter = ('date', 'currency', 'is_available', 'is_deleted', 'created_at')
    search_fields = ('rate_plan__name', 'notes')
    ordering = ('rate_plan', 'date')
    raw_id_fields = ('rate_plan',)
    
    def get_remaining_rooms(self, obj):
        """Display remaining rooms in admin list."""
        return obj.remaining_rooms
    get_remaining_rooms.short_description = 'Remaining Rooms'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('rate_plan', 'date')
        }),
        ('Inventory', {
            'fields': ('available_rooms', 'booked_rooms')
        }),
        ('Pricing', {
            'fields': ('price', 'currency')
        }),
        ('Availability Rules', {
            'fields': ('is_available', 'minimum_stay', 'maximum_stay')
        }),
        ('Additional Info', {
            'fields': ('notes',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted', 'deleted_at')
        }),
    )
