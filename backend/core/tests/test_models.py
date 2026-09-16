"""
Tests for core models.
"""
import pytest
from django.test import TestCase
from django.db import IntegrityError
from core.models import SystemSettings


class TestSystemSettings(TestCase):
    """Test cases for SystemSettings model."""
    
    def test_create_system_setting(self):
        """Test creating a system setting."""
        setting = SystemSettings.objects.create(
            key='test_key',
            value='test_value',
            description='Test description'
        )
        
        assert setting.key == 'test_key'
        assert setting.value == 'test_value'
        assert setting.description == 'Test description'
        assert setting.is_active is True
        assert setting.is_deleted is False
    
    def test_system_settings_str_representation(self):
        """Test string representation of SystemSettings."""
        setting = SystemSettings.objects.create(
            key='test_key',
            value='test_value'
        )
        
        expected_str = 'test_key: test_value'
        assert str(setting) == expected_str
    
    def test_system_settings_unique_key(self):
        """Test that key field is unique."""
        SystemSettings.objects.create(
            key='unique_key',
            value='value1'
        )
        
        # Attempting to create another setting with the same key should fail
        with pytest.raises(IntegrityError):
            SystemSettings.objects.create(
                key='unique_key',
                value='value2'
            )
    
    def test_system_settings_ordering(self):
        """Test that system settings are ordered by key."""
        SystemSettings.objects.create(key='zebra', value='value3')
        SystemSettings.objects.create(key='alpha', value='value1')
        SystemSettings.objects.create(key='beta', value='value2')
        
        settings = list(SystemSettings.objects.all())
        
        assert settings[0].key == 'alpha'
        assert settings[1].key == 'beta'
        assert settings[2].key == 'zebra'
