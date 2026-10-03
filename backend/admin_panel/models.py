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


class AppendOnlyQuerySet(models.QuerySet):
    """Bulk update/delete are refused, so audit rows cannot be rewritten in bulk either."""

    def update(self, **kwargs):
        raise PermissionError('Audit log entries cannot be changed')

    def delete(self):
        raise PermissionError('Audit log entries cannot be deleted')


class AdminAccessLog(models.Model):
    """
    Who on the staff opened which customer's data, and when (R4, audit #21).

    Ids only: no names, phones, emails or search terms, so the log itself holds no
    copy of personal data. Plain integer ids (not foreign keys) keep the history
    even if a user row is ever removed. Append-only: rows are never changed or deleted.
    """
    ACTION_CHOICES = [
        ('customer_list', 'Customer list'),
        ('customer_view', 'Customer profile'),
        ('booking_lookup', 'Support lookup by booking reference'),
        ('user_list', 'User list'),
        ('status_users', 'Status users list'),
        ('exchange_rate_accept', 'Accepted a rejected exchange rate'),
    ]

    actor_id = models.BigIntegerField(db_index=True, help_text='Staff user who opened the data')
    action = models.CharField(max_length=32, choices=ACTION_CHOICES, db_index=True)
    target_user_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    target_booking_id = models.BigIntegerField(null=True, blank=True)
    # Non-personal facts about the action (R6: currency, old and new rate of an accepted rate)
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        db_table = 'admin_access_log'
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.created_at} user:{self.actor_id} {self.action} target:{self.target_user_id}'

    @classmethod
    def record(cls, actor, action, target_user_id=None, target_booking_id=None, details=None):
        return cls.objects.create(
            actor_id=actor.pk, action=action,
            target_user_id=target_user_id, target_booking_id=target_booking_id, details=details,
        )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise PermissionError('Audit log entries cannot be changed')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError('Audit log entries cannot be deleted')
