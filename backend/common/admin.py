"""
Admin configuration for common models.
"""
from django.contrib import admin


class TimeStampedModelAdmin(admin.ModelAdmin):
    """
    Admin base class for timestamped models.
    """
    readonly_fields = ('created_at', 'updated_at')
    list_display = ('id', 'created_at', 'updated_at')
    
    def has_add_permission(self, request):
        return False


class SoftDeleteModelAdmin(admin.ModelAdmin):
    """
    Admin base class for soft-delete models.
    """
    readonly_fields = ('is_deleted', 'deleted_at')
    list_display = ('id', 'is_deleted', 'deleted_at')
    list_filter = ('is_deleted',)
    
    def has_add_permission(self, request):
        return False


class ActiveModelAdmin(admin.ModelAdmin):
    """
    Admin base class for active models.
    """
    list_display = ('id', 'is_active')
    list_filter = ('is_active',)


class BaseModelAdmin(TimeStampedModelAdmin, SoftDeleteModelAdmin, ActiveModelAdmin):
    """
    Combined admin class for base models.
    """
    readonly_fields = ('created_at', 'updated_at', 'is_deleted', 'deleted_at')
    list_display = ('id', 'is_active', 'is_deleted', 'created_at', 'updated_at')
    list_filter = ('is_active', 'is_deleted', 'created_at')
    
    def has_add_permission(self, request):
        return False
