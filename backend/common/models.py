"""
Common models and mixins for TICKBRON

This module contains base models and mixins that provide shared functionality
across all TICKBRON applications.
"""
from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides timestamp fields for creation and modification.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):
    """
    Abstract base model that provides soft delete functionality.
    Records are marked as deleted rather than being removed from the database.
    """
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def soft_delete(self):
        """Mark the record as deleted without removing it from the database."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class ActiveModel(models.Model):
    """
    Abstract base model that provides active/inactive status.
    """
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class BaseQuerySet(models.QuerySet):
    """
    Custom queryset with common filtering methods.
    """
    def active(self):
        """Return only active records."""
        return self.filter(is_active=True)
    
    def deleted(self):
        """Return only soft-deleted records."""
        return self.filter(is_deleted=True)
    
    def not_deleted(self):
        """Return only non-deleted records."""
        return self.filter(is_deleted=False)


class BaseModel(TimeStampedModel, SoftDeleteModel, ActiveModel):
    """
    Combined base model with timestamp, soft delete, and active status functionality.
    """
    objects = BaseQuerySet.as_manager()
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
