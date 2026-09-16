"""
Admin configuration for property models.
"""
from django.contrib import admin
from properties.models import PropertyType, Property, PropertyTranslation, PropertyPolicy


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


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """
    Admin interface for Property model.
    """
    list_display = ('id', 'owner', 'property_type', 'status', 'city', 'country', 'base_price', 'currency', 'max_guests', 'is_active', 'created_at')
    list_filter = ('status', 'property_type', 'country', 'currency', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('owner__email', 'city', 'country', 'address_line1')
    ordering = ('-created_at',)
    inlines = [PropertyTranslationInline, PropertyPolicyInline]
    
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
