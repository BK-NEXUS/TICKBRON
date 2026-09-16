"""
Core models for TICKBRON.

This module contains core application models that provide fundamental
functionality for the TICKBRON system.
"""
from django.db import models
from common.models import BaseModel


class SystemSettings(BaseModel):
    """
    System-wide settings and configuration.
    """
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value}"
