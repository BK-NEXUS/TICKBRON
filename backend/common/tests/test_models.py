"""
Tests for common models and mixins.
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from core.models import SystemSettings
from common.storage import get_media_upload_path, validate_image_file


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


class TestStorageAbstraction(TestCase):
    """Test cases for storage abstraction functions."""
    
    def test_get_media_upload_path_with_property(self):
        """Test get_media_upload_path with a property instance."""
        from properties.models import Property, PropertyType, PropertyPhoto
        from users.models import User
        from decimal import Decimal
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create test data
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )
        property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        property = Property.objects.create(
            owner=user,
            property_type=property_type,
            max_guests=4,
            address_line1='123 Test Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
        
        # Create a PropertyPhoto instance
        image = SimpleUploadedFile(
            name='test_photo.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b',
            content_type='image/jpeg'
        )
        photo = PropertyPhoto(property=property, photo=image)
        
        # Test path generation
        path = get_media_upload_path(photo, 'test_photo.jpg')
        expected_path = f'properties/{property.id}/photos/test_photo.jpg'
        assert path == expected_path
    
    def test_get_media_upload_path_without_property(self):
        """Test get_media_upload_path without a property instance (fallback)."""
        # Test with a mock instance that doesn't have property attribute
        class MockInstance:
            pass
        
        mock_instance = MockInstance()
        path = get_media_upload_path(mock_instance, 'test_photo.jpg')
        expected_path = 'properties/temp/photos/test_photo.jpg'
        assert path == expected_path
    
    def test_validate_image_file_valid_jpeg(self):
        """Test validate_image_file with a valid JPEG file."""
        valid_file = SimpleUploadedFile(
            name='test.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b',
            content_type='image/jpeg'
        )
        
        is_valid, error_message = validate_image_file(valid_file)
        assert is_valid is True
        assert error_message is None
    
    def test_validate_image_file_valid_png(self):
        """Test validate_image_file with a valid PNG file."""
        valid_file = SimpleUploadedFile(
            name='test.png',
            content=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82',
            content_type='image/png'
        )
        
        is_valid, error_message = validate_image_file(valid_file)
        assert is_valid is True
        assert error_message is None
    
    def test_validate_image_file_valid_gif(self):
        """Test validate_image_file with a valid GIF file."""
        valid_file = SimpleUploadedFile(
            name='test.gif',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b',
            content_type='image/gif'
        )
        
        is_valid, error_message = validate_image_file(valid_file)
        assert is_valid is True
        assert error_message is None
    
    def test_validate_image_file_valid_webp(self):
        """Test validate_image_file with a valid WebP file."""
        valid_file = SimpleUploadedFile(
            name='test.webp',
            content=b'RIFF\x24\x00\x00\x00WEBPVP8 \x14\x00\x00\x00\xd0\x02\x00\x9d\x01\x2a\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
            content_type='image/webp'
        )
        
        is_valid, error_message = validate_image_file(valid_file)
        assert is_valid is True
        assert error_message is None
    
    def test_validate_image_file_invalid_extension(self):
        """Test validate_image_file with invalid file extension."""
        invalid_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        
        is_valid, error_message = validate_image_file(invalid_file)
        assert is_valid is False
        assert 'File type .txt is not allowed' in error_message
    
    def test_validate_image_file_file_too_large(self):
        """Test validate_image_file with file exceeding size limit."""
        # Create a file larger than 10MB
        large_file = SimpleUploadedFile(
            name='large.jpg',
            content=b'x' * (11 * 1024 * 1024),  # 11MB
            content_type='image/jpeg'
        )
        
        is_valid, error_message = validate_image_file(large_file)
        assert is_valid is False
        assert 'File size exceeds maximum allowed size' in error_message
    
    def test_validate_image_file_invalid_content_type(self):
        """Test validate_image_file with invalid content type."""
        invalid_file = SimpleUploadedFile(
            name='test.jpg',
            content=b'This is not an image',
            content_type='application/pdf'
        )
        
        is_valid, error_message = validate_image_file(invalid_file)
        assert is_valid is False
        assert 'is not a valid image' in error_message
    
    def test_validate_image_file_at_size_limit(self):
        """Test validate_image_file at exactly the size limit (10MB)."""
        # Create a file exactly at 10MB
        limit_file = SimpleUploadedFile(
            name='limit.jpg',
            content=b'x' * (10 * 1024 * 1024),  # 10MB
            content_type='image/jpeg'
        )
        
        is_valid, error_message = validate_image_file(limit_file)
        assert is_valid is True
        assert error_message is None
