"""
core model leri ushın testler.
"""
import pytest
from django.test import TestCase
from django.db import IntegrityError
from core.models import SystemSettings


class TestSystemSettings(TestCase):
    """SystemSettings modeli ushın test jaǵdayları."""

    def test_create_system_setting(self):
        """Sistema sazlamasın jaratıwdı testlew."""
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
        """SystemSettings tiń qatar kórinisin testlew."""
        setting = SystemSettings.objects.create(
            key='test_key',
            value='test_value'
        )

        expected_str = 'test_key: test_value'
        assert str(setting) == expected_str

    def test_system_settings_unique_key(self):
        """key maydanı unikal ekenin testlew."""
        SystemSettings.objects.create(
            key='unique_key',
            value='value1'
        )

        # Sol key penen basqa sazlama jaratıwǵa urınıw sátsiz bolıwı kerek
        with pytest.raises(IntegrityError):
            SystemSettings.objects.create(
                key='unique_key',
                value='value2'
            )

    def test_system_settings_ordering(self):
        """Sistema sazlamaları key boyınsha tártiplengenin testlew."""
        SystemSettings.objects.create(key='zebra', value='value3')
        SystemSettings.objects.create(key='alpha', value='value1')
        SystemSettings.objects.create(key='beta', value='value2')

        settings = list(SystemSettings.objects.all())

        assert settings[0].key == 'alpha'
        assert settings[1].key == 'beta'
        assert settings[2].key == 'zebra'
