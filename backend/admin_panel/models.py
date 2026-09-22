"""
Admin models for TICKBRON.

This module contains models for admin-specific functionality.
Currently uses existing models from other apps with admin-specific
endpoints for moderation and management.
"""
from django.db import models
from django.core.validators import MinLengthValidator
from common.models import TimeStampedModel, SoftDeleteModel


class InternalNote(TimeStampedModel, SoftDeleteModel):
    """
    Internal notes for customers, visible only to staff/admins.
    
    These are staff-only free-text entries for customer management,
    fully CRUD-able, each stamped with the author (staff member) and timestamp.
    Never exposed to customers.
    """
    customer = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='internal_notes',
        db_index=True,
        help_text='Customer this note is about'
    )
    author = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_notes',
        help_text='Staff member who wrote this note'
    )
    note = models.TextField(
        validators=[MinLengthValidator(1)],
        help_text='Internal note content'
    )
    
    class Meta:
        db_table = 'internal_notes'
        verbose_name = 'Internal Note'
        verbose_name_plural = 'Internal Notes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['author', 'created_at']),
        ]
    
    def __str__(self):
        return f"Note for {self.customer.email} by {self.author.email if self.author else 'Unknown'}"
