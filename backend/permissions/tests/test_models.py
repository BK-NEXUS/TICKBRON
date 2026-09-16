"""
Tests for permission and role models.
"""
import pytest
from django.test import TestCase
from django.db import IntegrityError
from permissions.models import Role, Permission, RolePermission


class TestRoleModel(TestCase):
    """Test cases for Role model."""
    
    def test_create_role(self):
        """Test creating a role."""
        role = Role.objects.create(
            name='Customer',
            description='Regular customer role'
        )
        
        assert role.name == 'Customer'
        assert role.description == 'Regular customer role'
        assert role.is_system_role is False
        assert role.is_active is True
    
    def test_role_str_representation(self):
        """Test string representation of Role."""
        role = Role.objects.create(name='Admin')
        assert str(role) == 'Admin'
    
    def test_role_unique_name(self):
        """Test that role name is unique."""
        Role.objects.create(name='UniqueRole')
        
        with pytest.raises(IntegrityError):
            Role.objects.create(name='UniqueRole')
    
    def test_system_role_protection(self):
        """Test that system roles can be marked."""
        role = Role.objects.create(
            name='SystemAdmin',
            is_system_role=True
        )
        
        assert role.is_system_role is True


class TestPermissionModel(TestCase):
    """Test cases for Permission model."""
    
    def test_create_permission(self):
        """Test creating a permission."""
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
        """Test string representation of Permission."""
        permission = Permission.objects.create(
            name='View Properties',
            codename='view_properties',
            module='properties'
        )
        
        assert str(permission) == 'properties.view_properties'
    
    def test_permission_str_without_module(self):
        """Test string representation without module."""
        permission = Permission.objects.create(
            name='General Access',
            codename='general_access'
        )
        
        assert str(permission) == 'general_access'
    
    def test_permission_unique_codename(self):
        """Test that permission codename is unique."""
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
    """Test cases for RolePermission model."""
    
    def setUp(self):
        """Set up test data."""
        self.role = Role.objects.create(name='Customer')
        self.permission = Permission.objects.create(
            name='View Properties',
            codename='view_properties',
            module='properties'
        )
    
    def test_create_role_permission(self):
        """Test creating role-permission relationship."""
        role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission
        )
        
        assert role_permission.role == self.role
        assert role_permission.permission == self.permission
    
    def test_role_permission_str_representation(self):
        """Test string representation of RolePermission."""
        role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission
        )
        
        expected = f"{self.role.name} - {self.permission.name}"
        assert str(role_permission) == expected
    
    def test_role_permission_unique_constraint(self):
        """Test that role-permission combination is unique."""
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
        """Test that RolePermission inherits from BaseModel."""
        role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission
        )
        
        # Check BaseModel fields
        assert hasattr(role_permission, 'created_at')
        assert hasattr(role_permission, 'updated_at')
        assert hasattr(role_permission, 'is_deleted')
        assert hasattr(role_permission, 'is_active')