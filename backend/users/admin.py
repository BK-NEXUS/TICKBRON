"""
Admin configuration for user models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import User


class UserAdmin(BaseUserAdmin):
    """
    Admin interface for the custom User model.
    """
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'email_verified', 'two_factor_enabled', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_deleted', 'email_verified', 'two_factor_enabled')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Role', {'fields': ('role',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Security', {'fields': ('failed_login_attempts', 'last_failed_login', 'account_locked_until', 'last_login_ip')}),
        ('Verification', {'fields': ('email_verified', 'email_verification_token', 'email_verification_sent_at')}),
        ('Two-Factor Authentication', {'fields': ('two_factor_enabled', 'two_factor_secret', 'two_factor_backup_codes')}),
        ('Soft delete', {'fields': ('is_deleted', 'deleted_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


admin.site.register(User, UserAdmin)
