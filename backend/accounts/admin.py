"""
Admin configuration for the accounts app.
"""
from django.contrib import admin
from .models import Favorite, Review, Notification, AccountHistory


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Admin interface for Favorite model.
    """
    list_display = ['user', 'property', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'property__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for Review model.
    """
    list_display = ['user', 'property', 'overall_rating', 'status', 'created_at']
    list_filter = ['status', 'overall_rating', 'created_at']
    search_fields = ['user__email', 'property__name', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at', 'reviewed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'property', 'booking', 'status')
        }),
        ('Ratings', {
            'fields': ('overall_rating', 'cleanliness_rating', 'location_rating', 
                      'value_rating', 'amenities_rating', 'service_rating')
        }),
        ('Review Content', {
            'fields': ('title', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'reviewed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification model.
    """
    list_display = ['user', 'title', 'notification_type', 'priority', 'is_read', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at', 'updated_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'notification_type', 'priority', 'title', 'message')
        }),
        ('Related Objects', {
            'fields': ('booking', 'property')
        }),
        ('Delivery Status', {
            'fields': ('is_read', 'read_at', 'sent_via_email', 'sent_via_sms')
        }),
        ('Action Link', {
            'fields': ('action_url', 'action_label')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AccountHistory)
class AccountHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for AccountHistory model.
    """
    list_display = ['user', 'action', 'created_at', 'ip_address']
    list_filter = ['action', 'created_at']
    search_fields = ['user__email', 'description', 'ip_address']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'action', 'description')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Related Objects', {
            'fields': ('booking', 'property')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
