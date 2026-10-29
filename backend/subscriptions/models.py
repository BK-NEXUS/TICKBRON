"""The monthly fee a hotel pays the platform (plan .ai/PLAN_SUBSCRIPTION.md). The payment itself happens outside the site."""
from django.conf import settings
from django.db import models


class FeeSettings(models.Model):
    """One row: the amount every hotel pays each month, in whole UZS. 0 means not set yet, so nobody is billed."""
    monthly_amount = models.PositiveIntegerField(default=0)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]


class HotelFeeAccount(models.Model):
    """When a hotel's free period ends. Created once, when the hotel first becomes active."""
    property = models.OneToOneField('properties.Property', on_delete=models.CASCADE, related_name='fee_account')
    free_until = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)


class MonthlyFee(models.Model):
    STATUS_DUE = 'due'
    STATUS_PAID = 'paid'
    STATUS_CHOICES = [(STATUS_DUE, 'Due'), (STATUS_PAID, 'Paid')]

    VIA_PANEL = 'panel'
    VIA_CHOICES = [(VIA_PANEL, 'Admin panel')]

    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='monthly_fees')
    month = models.DateField(help_text='First day of the month; also the due date')
    amount = models.PositiveIntegerField(help_text='UZS, copied from the setting when the fee was created')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DUE, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    confirmed_via = models.CharField(max_length=10, choices=VIA_CHOICES, blank=True, default='')
    note = models.CharField(max_length=200, blank=True, default='')
    reminder_stage = models.PositiveSmallIntegerField(default=0, help_text='How many reminders the owner got (0-3)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['property', 'month'], name='one_fee_per_hotel_and_month')]
        ordering = ['-month', 'id']
