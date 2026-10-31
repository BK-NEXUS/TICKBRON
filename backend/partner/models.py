"""
Partner models for TICKBRON.

This module contains models for partner/hotel-owner property management.
Currently uses existing Property, RoomType, RatePlan, DateInventory models
from properties app with owner-based scoping.
"""

from django.conf import settings
from django.db import models

from common.models import BaseModel


class OwnerPlace(BaseModel):
    """
    Where the hotels of a hotel-owner account appear (country > region > city): chosen by the super admin
    when the account is created. The owner's hotels are created in this place and the owner cannot move them.
    PROTECT: a place in use by an account is hidden, never deleted.
    """
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_place')
    country = models.ForeignKey('geography.Country', on_delete=models.PROTECT, related_name='+')
    region = models.ForeignKey('geography.Region', on_delete=models.PROTECT, related_name='+')
    city = models.ForeignKey('geography.City', on_delete=models.PROTECT, related_name='+')

    class Meta:
        db_table = 'partner_owner_places'


class CommissionRate(models.Model):
    """
    The percent of each counted booking that the site takes from a hotel owner, from the first day of
    `effective_from` (always a month start). One row per owner per month; the rate of a month is the latest
    row not after it, so a change never rewrites an earlier month and an owner with no row has no commission.
    """
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commission_rates')
    percent = models.DecimalField(max_digits=5, decimal_places=2)
    effective_from = models.DateField()
    set_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'partner_commission_rates'
        ordering = ['effective_from']
        constraints = [
            models.UniqueConstraint(fields=['owner', 'effective_from'], name='commission_rate_owner_month_unique'),
            models.CheckConstraint(condition=models.Q(percent__gte=0, percent__lte=100), name='commission_rate_percent_range'),
        ]


class CommissionPayment(models.Model):
    """
    "This owner paid the commission of this month", confirmed by a super admin or a staff admin. The name and
    role of the confirmer and the amounts are copied here, so the record stays true if the account is renamed
    or later bookings change the month's figures.
    """
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commission_payments')
    month = models.DateField()
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+')
    confirmed_by_name = models.CharField(max_length=300)
    confirmed_by_role = models.CharField(max_length=20)
    confirmed_at = models.DateTimeField(auto_now_add=True)
    amounts = models.JSONField()

    class Meta:
        db_table = 'partner_commission_payments'
        ordering = ['-month']
        constraints = [
            models.UniqueConstraint(fields=['owner', 'month'], name='commission_payment_owner_month_unique'),
        ]
