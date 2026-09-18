from django.contrib import admin
from .models import Booking, BookingItem


class BookingItemInline(admin.TabularInline):
    """Inline admin for booking items."""
    model = BookingItem
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['room_type', 'rate_plan', 'number_of_rooms', 'price_per_night', 'currency']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for Booking model."""
    list_display = [
        'confirmation_code', 'guest', 'property', 'status', 'payment_status',
        'check_in', 'check_out', 'total_price', 'currency', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at', 'check_in', 'check_out']
    search_fields = ['confirmation_code', 'guest__email', 'guest__first_name', 'guest__last_name']
    readonly_fields = ['confirmation_code', 'created_at', 'updated_at', 'cancelled_at']
    inlines = [BookingItemInline]
    fieldsets = (
        ('Guest Information', {
            'fields': ('guest',)
        }),
        ('Property Information', {
            'fields': ('property',)
        }),
        ('Booking Details', {
            'fields': ('status', 'payment_status', 'check_in', 'check_out', 'number_of_nights', 'guest_count')
        }),
        ('Pricing', {
            'fields': ('total_price', 'currency')
        }),
        ('Additional Information', {
            'fields': ('special_requests', 'confirmation_code')
        }),
        ('Cancellation Information', {
            'fields': ('cancelled_at', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookingItem)
class BookingItemAdmin(admin.ModelAdmin):
    """Admin interface for BookingItem model."""
    list_display = ['id', 'booking', 'room_type', 'rate_plan', 'number_of_rooms', 'price_per_night', 'currency']
    list_filter = ['room_type', 'rate_plan', 'currency']
    search_fields = ['booking__confirmation_code', 'room_type__name', 'rate_plan__name']
    readonly_fields = ['created_at', 'updated_at']
