"""
Ruxsat hám rol model leri ushın testler.
"""
import pytest
from django.test import TestCase
from django.db import IntegrityError
from permissions.models import Role, Permission, RolePermission


class TestRoleModel(TestCase):
    """Role modeli ushın test jaǵdayları."""

    def test_create_role(self):
        """Rol jaratıwdı testlew."""
        role = Role.objects.create(
            name='Customer',
            description='Regular customer role'
        )

        assert role.name == 'Customer'
        assert role.description == 'Regular customer role'
        assert role.is_system_role is False
        assert role.is_active is True

    def test_role_str_representation(self):
        """Role tiń qatar kórinisin testlew."""
        role = Role.objects.create(name='Admin')
        assert str(role) == 'Admin'

    def test_role_unique_name(self):
        """Rol atı unikal ekenin testlew."""
        Role.objects.create(name='UniqueRole')

        with pytest.raises(IntegrityError):
            Role.objects.create(name='UniqueRole')

    def test_system_role_protection(self):
        """Sistema rolleri belgilene alatuǵının testlew."""
        role = Role.objects.create(
            name='SystemAdmin',
            is_system_role=True
        )

        assert role.is_system_role is True


class TestPermissionModel(TestCase):
    """Permission modeli ushın test jaǵdayları."""

    def test_create_permission(self):
        """Ruxsat jaratıwdı testlew."""
        permission = Permission.objects.create(
            name='View Properties',
            codename='view_properties',
            module='properties',
            description='Can view property listings'
        )

        assert permission.name == 'View Properties'
        assert permission.codename == 'view_properties'
        assert permission.module == 'properties'
        assert permission.description == 'Can view property listings'

    def test_permission_str_representation(self):
        """Permission niń qatar kórinisin testlew."""
        permission = Permission.objects.create(
            name='View Properties',
            codename='view_properties',
            module='properties'
        )

        assert str(permission) == 'properties.view_properties'

    def test_permission_str_without_module(self):
        """Modulsiz qatar kórinisin testlew."""
        permission = Permission.objects.create(
            name='General Access',
            codename='general_access'
        )

        assert str(permission) == 'general_access'

    def test_permission_unique_codename(self):
        """Ruxsat codename i unikal ekenin testlew."""
        Permission.objects.create(
            name='Test Permission',
            codename='test_permission'
        )

        with pytest.raises(IntegrityError):
            Permission.objects.create(
                name='Another Test',
                codename='test_permission'
            )


class TestRolePermissionModel(TestCase):
    """RolePermission modeli ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.role = Role.objects.create(name='Customer')
        self.permission = Permission.objects.create(
            name='View Properties',
            codename='view_properties',
            module='properties'
        )

    def test_create_role_permission(self):
        """Rol-ruxsat baylanısın jaratıwdı testlew."""
        role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission
        )

        assert role_permission.role == self.role
        assert role_permission.permission == self.permission

    def test_role_permission_str_representation(self):
        """RolePermission niń qatar kórinisin testlew."""
        role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission
        )

        expected = f"{self.role.name} - {self.permission.name}"
        assert str(role_permission) == expected

    def test_role_permission_unique_constraint(self):
        """Rol-ruxsat kombinaciyası unikal ekenin testlew."""
        RolePermission.objects.create(
            role=self.role,
            permission=self.permission
        )

        with pytest.raises(IntegrityError):
            RolePermission.objects.create(
                role=self.role,
                permission=self.permission
            )

    def test_role_inherits_base_model(self):
        """RolePermission BaseModel den miras alatuǵının testlew."""
        role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission
        )

        # BaseModel maydanların tekseriw
        assert hasattr(role_permission, 'created_at')
        assert hasattr(role_permission, 'updated_at')
        assert hasattr(role_permission, 'is_deleted')
        assert hasattr(role_permission, 'is_active')
