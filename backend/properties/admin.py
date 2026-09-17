"""
Admin configuration for property models.
"""
from django.contrib import admin
from properties.models import (
    PropertyType, Property, PropertyTranslation, PropertyPolicy,
    AmenityCategory, AmenityCategoryTranslation, Amenity, AmenityTranslation, PropertyAmenity
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


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """
    Admin interface for Property model.
    """
    list_display = ('id', 'owner', 'property_type', 'status', 'city', 'country', 'base_price', 'currency', 'max_guests', 'is_active', 'created_at')
    list_filter = ('status', 'property_type', 'country', 'currency', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('owner__email', 'city', 'country', 'address_line1')
    ordering = ('-created_at',)
    inlines = [PropertyTranslationInline, PropertyPolicyInline, PropertyAmenityInline]
    
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
