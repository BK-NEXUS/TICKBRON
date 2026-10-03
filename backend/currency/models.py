"""
Exchange rate history (R6). Rows are appended by the scheduled CBU fetch (and by a
super-admin accepting a rejected rate); they are never changed or deleted, so any
booking's snapshot can be traced back to the row it came from.
"""
from django.db import models
from django.utils import timezone

from admin_panel.models import AppendOnlyQuerySet


class AppendOnlyModel(models.Model):
    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise PermissionError(f'{type(self).__name__} rows cannot be changed')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError(f'{type(self).__name__} rows cannot be deleted')


class ExchangeRate(AppendOnlyModel):
    """UZS per one unit of `currency` (CBU Rate / Nominal), for one CBU rate date."""
    STATUS_CHOICES = [('accepted', 'Accepted'), ('rejected', 'Rejected')]

    currency = models.CharField(max_length=3, db_index=True)
    rate = models.DecimalField(max_digits=18, decimal_places=6)
    nominal = models.PositiveIntegerField(default=1)
    rate_date = models.DateField(db_index=True)
    source = models.CharField(max_length=32, default='cbu.uz')
    fetched_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, db_index=True)
    note = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'exchange_rates'
        ordering = ['-rate_date', '-fetched_at', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['currency', 'rate_date', 'source'], condition=models.Q(status='accepted'),
                name='one_accepted_rate_per_day',
            ),
        ]

    def __str__(self):
        return f'{self.currency} {self.rate} ({self.rate_date}, {self.status})'


class ExchangeRateFetch(AppendOnlyModel):
    """One row per fetch attempt and currency, so staff can see the last error."""
    currency = models.CharField(max_length=3)
    attempted_at = models.DateTimeField(default=timezone.now, db_index=True)
    success = models.BooleanField()
    error = models.CharField(max_length=255, blank=True, default='')
    exchange_rate = models.ForeignKey(ExchangeRate, null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        db_table = 'exchange_rate_fetches'
        ordering = ['-attempted_at', '-id']
