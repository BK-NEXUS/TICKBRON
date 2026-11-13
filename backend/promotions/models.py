"""
Mehmanxanalardıń banner karuselinde tólengen orınlastırıwı (R10).

Bir `Promotion` qatarı bir mehmanxananıń bir tólengen dáwiri. Baha tek super-admin
esap ushın jazǵan kelisilgen summa; bron yamasa tólemde hesh nárse onı oqımaydı.
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
    # Usı statuslardıń birindegi dáwir óz sanaların kesilisiwge qarsı ele ustap turadı
    HOLDING_STATUSES = (STATUS_SCHEDULED, STATUS_ACTIVE, STATUS_PAUSED)

    property = models.ForeignKey('properties.Property', on_delete=models.PROTECT, related_name='promotions')
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True, help_text='Inclusive, business dates (Asia/Tashkent)')
    priority = models.PositiveSmallIntegerField(default=0, help_text='0-100, higher is shown first')

    # Bos = hár jerde kórsetiledi; belgilengen dáreje onı sol orındaǵı mehmanxanalarǵa shekemleydi
    country_ref = models.ForeignKey(
        'geography.Country', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    region_ref = models.ForeignKey(
        'geography.Region', on_delete=models.PROTECT, null=True, blank=True, related_name='+')

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
        indexes = [
            models.Index(fields=['property', 'start_date', 'end_date'], name='promo_prop_dates_idx'),
            # Házir kórsetilip atırǵan reklama: status hám sana oynası
            models.Index(fields=['status', 'start_date', 'end_date'], name='promo_status_dates_idx'),
        ]

    def __str__(self):
        return f'Promotion {self.pk} property:{self.property_id} {self.start_date}..{self.end_date}'


class AdRenewal(models.Model):
    """
    Reklamanıń ayı pitkende soralatuǵın soraw: mehmanxana keyingisi ushın tóledi me? Pitken kúni ashıladı;
    reklama `deadline` ǵa shekem kórinip turadı; sol waqıtqa shekem tastıyıqlaw bolmasa onı alıp taslaydı
    (promotions/renewals.py).
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
    """Bir promotion nıń bir is kúnindegi kóriwleri hám bosıwları. Kelwshi maǵlıwmatı saqlanbaydı."""
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField(db_index=True)
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'promotion_daily_stats'
        constraints = [models.UniqueConstraint(fields=['promotion', 'date'], name='promo_stat_unique_day')]
        ordering = ['-date']


def promotion_photo_path(instance, filename):
    """Klienttiń fayl atı hesh qashan paydalanılmaydı: saqlanǵan jollar ashıq hám boljawǵa bolmaytuǵın bolıwı kerek."""
    return f'promotions/{instance.promotion_id}/{uuid.uuid4().hex}{os.path.splitext(filename)[1].lower()}'


class PromotionPhoto(BaseModel):
    """Super-admin bir reklamaǵa qoyǵan súwret; banner mehmanxananıń óz súwretleriniń ornına usılardı kórsetedi."""
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to=promotion_photo_path)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'promotion_photos'
        ordering = ['display_order', 'id']

    def __str__(self):
        return f'PromotionPhoto {self.pk} promotion:{self.promotion_id}'
