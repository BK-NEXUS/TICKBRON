"""
TICKBRON ushın ruxsat hám rol model leri.

Bul modul rol tiykarındaǵı kirisiwdi basqarıw (RBAC) tiykarınıń model lerin óz ishine aladı.
"""
from django.db import models
from common.models import BaseModel


class Role(BaseModel):
    """
    RBAC tiykarı ushın Role modeli.

    Baylanıslı ruxsatları bar paydalanıwshı rollerin anıqlaydı.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    is_system_role = models.BooleanField(default=False)  # Sistema rolleri óshirilmeydi

    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']

    def __str__(self):
        return self.name


class Permission(BaseModel):
    """
    RBAC tiykarı ushın Permission modeli.

    Rollerge berilip atırılatuǵın mayda ruxsatlardı anıqlaydı.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    codename = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    module = models.CharField(max_length=100, blank=True, null=True)  # mısalı, 'properties', 'bookings'

    class Meta:
        db_table = 'permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['module', 'name']

    def __str__(self):
        return f"{self.module}.{self.codename}" if self.module else self.codename


class RolePermission(BaseModel):
    """
    Rollar menen ruxsatlar arasındaǵı many-to-many baylanıs.
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
