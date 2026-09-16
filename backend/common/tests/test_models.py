"""
Tests for common models and mixins.
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from core.models import SystemSettings


class TestBaseModelFunctionality(TestCase):
    """Test cases for BaseModel functionality (via SystemSettings)."""
    
    def test_created_at_auto_populated(self):
        """Test that created_at is automatically populated."""
        setting = SystemSettings.objects.create(
            key='test_key',
            value='test_value'
        )
        
        assert setting.created_at is not None
        assert isinstance(setting.created_at, timezone.datetime)
    
    def test_updated_at_auto_populated(self):
        """Test that updated_at is automatically populated."""
        setting = SystemSettings.objects.create(
            key='test_key',
            value='test_value'
        )
        
        assert setting.updated_at is not None
        assert isinstance(setting.updated_at, timezone.datetime)
    
    def test_soft_delete_functionality(self):
        """Test that soft delete marks record as deleted."""
        setting = SystemSettings.objects.create(
            key='test_key',
            value='test_value'
        )
        
        setting.soft_delete()
        setting.refresh_from_db()
        
        assert setting.is_deleted is True
        assert setting.deleted_at is not None
    
    def test_restore_functionality(self):
        """Test that restore unmarks record as deleted."""
        setting = SystemSettings.objects.create(
            key='test_key',
            value='test_value'
        )
        
        setting.soft_delete()
        setting.restore()
        setting.refresh_from_db()
        
        assert setting.is_deleted is False
        assert setting.deleted_at is None
    
    def test_is_active_default(self):
        """Test that is_active defaults to True."""
        setting = SystemSettings.objects.create(
            key='test_key',
            value='test_value'
        )
        
        assert setting.is_active is True


class TestBaseQuerySet(TestCase):
    """Test cases for BaseQuerySet."""
    
    def test_active_filter(self):
        """Test the active() queryset method."""
        # Create active and inactive records
        active_setting = SystemSettings.objects.create(
            key='active_key',
            value='active_value',
            is_active=True
        )
        inactive_setting = SystemSettings.objects.create(
            key='inactive_key',
            value='inactive_value',
            is_active=False
        )
        
        active_records = SystemSettings.objects.active()
        
        assert active_setting in active_records
        assert inactive_setting not in active_records
    
    def test_deleted_filter(self):
        """Test the deleted() queryset method."""
        # Create normal and deleted records
        normal_setting = SystemSettings.objects.create(
            key='normal_key',
            value='normal_value'
        )
        deleted_setting = SystemSettings.objects.create(
            key='deleted_key',
            value='deleted_value'
        )
        deleted_setting.soft_delete()
        
        deleted_records = SystemSettings.objects.deleted()
        
        assert deleted_setting in deleted_records
        assert normal_setting not in deleted_records
    
    def test_not_deleted_filter(self):
        """Test the not_deleted() queryset method."""
        # Create normal and deleted records
        normal_setting = SystemSettings.objects.create(
            key='normal_key',
            value='normal_value'
        )
        deleted_setting = SystemSettings.objects.create(
            key='deleted_key',
            value='deleted_value'
        )
        deleted_setting.soft_delete()
        
        not_deleted_records = SystemSettings.objects.not_deleted()
        
        assert normal_setting in not_deleted_records
        assert deleted_setting not in not_deleted_records
