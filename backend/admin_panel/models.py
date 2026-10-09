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
        ('refund_mark_done', 'Marked a manual refund as paid'),
        ('refund_retry', 'Retried a failed refund'),
        ('status_user_view', 'Status: one guest'),
        ('export_csv', 'CSV export'),
        ('no_show_report_approve', 'Approved a no-show report'),
        ('no_show_report_reject', 'Rejected a no-show report'),
        ('no_show_report_reverse', 'Corrected a no-show report decision'),
        ('promotion_create', 'Created a hotel promotion'),
        ('promotion_update', 'Changed a hotel promotion'),
        ('promotion_pause', 'Paused a hotel promotion'),
        ('promotion_resume', 'Resumed a hotel promotion'),
        ('promotion_cancel', 'Cancelled a hotel promotion'),
        ('promotion_mark_paid', 'Recorded the payment of a hotel promotion'),
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

    # The only keys `details` may hold: non-personal facts, flat scalar values
    DETAIL_KEYS = frozenset({'currency', 'rate_date', 'old_rate', 'new_rate', 'rejected_id', 'accepted_id',
                             'refund_id', 'export', 'rows', 'report_id',
                             'promotion_id', 'property_id', 'start_date', 'end_date', 'amount'})

    @classmethod
    def _check_details(cls, details):
        if details is None:
            return
        if not isinstance(details, dict):
            raise ValueError('Audit details must be a dict')
        unknown = set(details) - cls.DETAIL_KEYS
        if unknown:
            raise ValueError(f'Audit details keys not allowed: {sorted(unknown)}')
        for value in details.values():
            if value is not None and not isinstance(value, (str, int)):
                raise ValueError('Audit details values must be text, integers or null')

    @classmethod
    def record(cls, actor, action, target_user_id=None, target_booking_id=None, details=None):
        cls._check_details(details)
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
