"""
Storage abstraction for TICKBRON media handling.

This module provides a unified storage interface that works across different environments:
- Local filesystem for development
- S3-compatible storage for staging/production
"""
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class TickBronStorage:
    """
    Unified storage abstraction for TICKBRON media files.
    
    This class provides a consistent interface for media storage across different
    environments (local, staging, production) while allowing environment-specific
    implementations.
    """
    
    def __init__(self):
        self._storage_backend = self._get_storage_backend()
    
    def _get_storage_backend(self):
        """
        Determine the appropriate storage backend based on environment.
        
        Returns:
            Storage backend instance (FileSystemStorage, S3Storage, etc.)
        """
        storage_type = getattr(settings, 'STORAGE_TYPE', 'local')
        
        if storage_type == 'local':
            return LocalStorage()
        elif storage_type == 's3':
            return S3Storage()
        else:
            # Default to local storage
            return LocalStorage()
    
    def url(self, name):
        """Get URL for the given file name."""
        return self._storage_backend.url(name)
    
    def path(self, name):
        """Get local filesystem path for the given file name."""
        return self._storage_backend.path(name)
    
    def exists(self, name):
        """Check if a file exists."""
        return self._storage_backend.exists(name)
    
    def save(self, name, content, max_length=None):
        """Save a file."""
        return self._storage_backend.save(name, content, max_length=max_length)
    
    def delete(self, name):
        """Delete a file."""
        return self._storage_backend.delete(name)
    
    def listdir(self, path):
        """List contents of a directory."""
        return self._storage_backend.listdir(path)
    
    def size(self, name):
        """Get file size in bytes."""
        return self._storage_backend.size(name)
    
    def get_available_name(self, name, max_length=None):
        """Get an available filename for the given name."""
        return self._storage_backend.get_available_name(name, max_length)
    
    def generate_filename(self, filename):
        """Generate a unique filename for the given filename."""
        return self._storage_backend.generate_filename(filename)


class LocalStorage(FileSystemStorage):
    """
    Local filesystem storage for development.
    
    This storage backend stores files on the local filesystem and is suitable
    for development and testing environments.
    """
    
    def __init__(self):
        location = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        base_url = getattr(settings, 'MEDIA_URL', '/media/')
        
        super().__init__(
            location=location,
            base_url=base_url
        )
    
    def get_available_name(self, name, max_length=None):
        """
        Get an available filename while preserving the original file extension.
        
        This method ensures that uploaded files maintain their original extensions
        while avoiding name collisions.
        """
        # Split the name into base and extension
        base, ext = os.path.splitext(name)
        
        # If the name is already available, return it
        if not self.exists(name):
            return name
        
        # Otherwise, add a counter to make it unique
        counter = 1
        while True:
            new_name = f"{base}_{counter}{ext}"
            if not self.exists(new_name):
                return new_name
            counter += 1


class S3Storage:
    """
    S3-compatible storage for staging/production.
    
    This storage backend uses S3-compatible object storage (AWS S3, MinIO, etc.)
    for production environments. Placeholder implementation - requires boto3.
    
    Note: This is a placeholder. In production, you would use django-storages
    with proper S3 configuration.
    """
    
    def __init__(self):
        # Placeholder for S3 configuration
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'tickbron-media')
        self.access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', '')
        self.secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')
        self.region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        self.custom_domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)
    
    def url(self, name):
        """Get URL for the given file name."""
        if self.custom_domain:
            return f"https://{self.custom_domain}/{name}"
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{name}"
    
    def path(self, name):
        """S3 storage doesn't have local paths."""
        raise NotImplementedError("S3 storage doesn't support local paths")
    
    def exists(self, name):
        """Check if a file exists in S3."""
        # Placeholder implementation
        # In production, this would use boto3 to check S3
        return False
    
    def save(self, name, content, max_length=None):
        """Save a file to S3."""
        # Placeholder implementation
        # In production, this would use boto3 to upload to S3
        raise NotImplementedError("S3 storage not yet implemented")
    
    def delete(self, name):
        """Delete a file from S3."""
        # Placeholder implementation
        # In production, this would use boto3 to delete from S3
        raise NotImplementedError("S3 storage not yet implemented")
    
    def listdir(self, path):
        """List contents of an S3 directory."""
        # Placeholder implementation
        # In production, this would use boto3 to list S3 objects
        raise NotImplementedError("S3 storage not yet implemented")
    
    def size(self, name):
        """Get file size from S3."""
        # Placeholder implementation
        # In production, this would use boto3 to get S3 object size
        raise NotImplementedError("S3 storage not yet implemented")
    
    def get_available_name(self, name, max_length=None):
        """Get an available filename for S3."""
        # S3 handles naming differently, but we'll use similar logic
        base, ext = os.path.splitext(name)
        counter = 1
        while True:
            new_name = f"{base}_{counter}{ext}"
            if not self.exists(new_name):
                return new_name
            counter += 1
    
    def generate_filename(self, filename):
        """Generate a unique filename for S3."""
        return self.get_available_name(filename)


def get_storage():
    """
    Get the appropriate storage instance for the current environment.
    
    Returns:
        TickBronStorage instance configured for the current environment
    """
    return TickBronStorage()


def get_media_upload_path(instance, filename):
    """
    Generate upload path for property media files.
    
    Args:
        instance: The model instance (PropertyPhoto)
        filename: The original filename
    
    Returns:
        Path string for storing the file
    """
    if hasattr(instance, 'property'):
        property_id = instance.property.id
    else:
        # Fallback if property is not set yet
        property_id = 'temp'
    
    # Generate path: properties/{property_id}/photos/{filename}
    return f'properties/{property_id}/photos/{filename}'


def validate_image_file(file):
    """
    Validate uploaded image files.
    
    Args:
        file: UploadedFile instance
    
    Returns:
        tuple (is_valid, error_message)
    """
    from django.core.exceptions import ValidationError
    
    # Check file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        return False, f"File size exceeds maximum allowed size of {max_size / (1024*1024)}MB"
    
    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_ext = os.path.splitext(file.name)[1].lower()
    if file_ext not in allowed_extensions:
        return False, f"File type {file_ext} is not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check if file is actually an image (basic check)
    if not file.content_type.startswith('image/'):
        return False, f"File content type {file.content_type} is not a valid image"
    
    return True, None