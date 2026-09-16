"""
Custom managers for TICKBRON models.

This module contains custom managers that provide additional query capabilities.
"""
from django.db import models


class SoftDeleteManager(models.Manager):
    """
    Manager that excludes soft-deleted records by default.
    """
    def get_queryset(self):
        """Return queryset excluding soft-deleted records."""
        return super().get_queryset().filter(is_deleted=False)


class ActiveManager(models.Manager):
    """
    Manager that returns only active records.
    """
    def get_queryset(self):
        """Return queryset with only active records."""
        return super().get_queryset().filter(is_active=True)
