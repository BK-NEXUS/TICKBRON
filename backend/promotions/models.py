"""
Paid placement of hotels in the banner carousel (R10).

One `Promotion` row is one paid period of one hotel. The price is only the agreed amount
typed by the super-admin for the books; nothing in booking or payment reads it.
"""
import os
import uuid

from django.conf import settings
from django.db import models

from common.models import BaseModel


class Promotion(BaseModel):
    STATUS_SCHEDULED = 'scheduled'
    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_ENDED = 'ended'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_PAUSED, 'Paused'),
        (STATUS_ENDED, 'Ended'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    # A period in one of these statuses still holds its dates against overlaps
    HOLDING_STATUSES = (STATUS_SCHEDULED, STATUS_ACTIVE, STATUS_PAUSED)

    property = models.ForeignKey('properties.Property', on_delete=models.PROTECT, related_name='promotions')
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True, help_text='Inclusive, business dates (Asia/Tashkent)')
    priority = models.PositiveSmallIntegerField(default=0, help_text='0-100, higher is shown first')

    # Empty = shown everywhere; a set level limits it to hotels in that place
    country_ref = models.ForeignKey(
        'geography.Country', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    region_ref = models.ForeignKey(
        'geography.Region', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    city_ref = models.ForeignKey(
        'geography.City', on_delete=models.PROTECT, null=True, blank=True, related_name='+')

    price_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    price_currency = models.CharField(max_length=3, default='UZS')
    note = models.CharField(max_length=500, blank=True, default='')

    paid_at = models.DateTimeField(null=True, blank=True)
    paid_marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_SCHEDULED, db_index=True)
    cancelled_reason = models.CharField(max_length=255, blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        db_table = 'promotions'
        ordering = ['-start_date', '-id']
        indexes = [models.Index(fields=['property', 'start_date', 'end_date'], name='promo_prop_dates_idx')]

    def __str__(self):
        return f'Promotion {self.pk} property:{self.property_id} {self.start_date}..{self.end_date}'


class AdRenewal(models.Model):
    """
    The question asked when an ad's month ends: did the hotel pay for the next one? Opened on the end day;
    the ad stays visible until `deadline`; no confirmation by then removes it (promotions/renewals.py).
    """
    STATUS_PENDING = 'pending'
    STATUS_RENEWED = 'renewed'
    STATUS_DECLINED = 'declined'
    STATUS_EXPIRED = 'expired'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Waiting for the answer'),
        (STATUS_RENEWED, 'Renewed for one more month'),
        (STATUS_DECLINED, 'Declined, ad removed'),
        (STATUS_EXPIRED, 'No answer in time, ad removed'),
    ]
    VIA_PANEL = 'panel'
    VIA_TELEGRAM = 'telegram'
    VIA_AUTO = 'auto'
    VIA_CHOICES = [(VIA_PANEL, 'Admin panel'), (VIA_TELEGRAM, 'Telegram'), (VIA_AUTO, 'Automatic')]

    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='renewals')
    ends_on = models.DateField(help_text='The end date being renewed')
    deadline = models.DateField(help_text='Inclusive: the last day the ad stays visible without an answer')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reminder_stage = models.PositiveSmallIntegerField(default=0, help_text='Notices sent to the owner (0-2)')
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    decided_via = models.CharField(max_length=10, choices=VIA_CHOICES, blank=True, default='')
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'promotion_renewals'
        ordering = ['deadline', 'id']
        constraints = [models.UniqueConstraint(fields=['promotion', 'ends_on'], name='promo_renewal_unique_end')]
        indexes = [models.Index(fields=['status', 'deadline'], name='promo_renewal_status_idx')]

    def __str__(self):
        return f'AdRenewal {self.pk} promotion:{self.promotion_id} ends:{self.ends_on} {self.status}'


class PromotionDailyStat(models.Model):
    """Views and clicks of one promotion on one business date. No visitor data is stored."""
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField(db_index=True)
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'promotion_daily_stats'
        constraints = [models.UniqueConstraint(fields=['promotion', 'date'], name='promo_stat_unique_day')]
        ordering = ['-date']


def promotion_photo_path(instance, filename):
    """The client's file name is never used: stored paths are public and must not be guessable."""
    return f'promotions/{instance.promotion_id}/{uuid.uuid4().hex}{os.path.splitext(filename)[1].lower()}'


class PromotionPhoto(BaseModel):
    """A picture the super-admin put on one ad; the banner shows these instead of the hotel's own photos."""
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to=promotion_photo_path)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'promotion_photos'
        ordering = ['display_order', 'id']

    def __str__(self):
        return f'PromotionPhoto {self.pk} promotion:{self.promotion_id}'
