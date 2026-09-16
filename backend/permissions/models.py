"""
Permission and role models for TICKBRON.

This module contains models for role-based access control (RBAC) foundation.
"""
from django.db import models
from common.models import BaseModel


class Role(BaseModel):
    """
    Role model for RBAC foundation.
    
    Defines user roles with associated permissions.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    is_system_role = models.BooleanField(default=False)  # System roles cannot be deleted
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Permission(BaseModel):
    """
    Permission model for RBAC foundation.
    
    Defines granular permissions that can be assigned to roles.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    codename = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    module = models.CharField(max_length=100, blank=True, null=True)  # e.g., 'properties', 'bookings'
    
    class Meta:
        db_table = 'permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['module', 'name']
    
    def __str__(self):
        return f"{self.module}.{self.codename}" if self.module else self.codename


class RolePermission(BaseModel):
    """
    Many-to-many relationship between roles and permissions.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='permission_roles')
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ('role', 'permission')
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"
