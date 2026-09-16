"""
Admin configuration for permission models.
"""
from django.contrib import admin
from permissions.models import Role, Permission, RolePermission


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Admin interface for Role model.
    """
    list_display = ('name', 'description', 'is_system_role', 'is_active', 'created_at')
    list_filter = ('is_system_role', 'is_active', 'is_deleted')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of system roles."""
        if obj and obj.is_system_role:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """
    Admin interface for Permission model.
    """
    list_display = ('name', 'codename', 'module', 'description', 'is_active', 'created_at')
    list_filter = ('module', 'is_active', 'is_deleted')
    search_fields = ('name', 'codename', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """
    Admin interface for RolePermission model.
    """
    list_display = ('role', 'permission', 'is_active', 'created_at')
    list_filter = ('role', 'permission__module', 'is_active', 'is_deleted')
    search_fields = ('role__name', 'permission__name', 'permission__codename')
    readonly_fields = ('created_at', 'updated_at')
