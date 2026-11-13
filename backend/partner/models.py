"""
TICKBRON ushın partner model leri.

Bul modul partner/mehmanxana iyesi mehmanxanalardı basqarıw model lerin óz ishine aladı.
Házir properties app ınan bar Property, RoomType, RatePlan, DateInventory model leri
iye boyınsha shekemlenip paydalanıladı.
"""

from django.conf import settings
from django.db import models

from common.models import BaseModel


class OwnerPlace(BaseModel):
    """
    Mehmanxana iyesi akkauntınıń mehmanxanaları qayerde kórinedi (mámleket > region): super admin tańlaydı,
    akkaunt jaratılǵanda. Iyeniń mehmanxanaları usı orında jaratıladı hám iye olardı kóshire almaydı.
    PROTECT: akkaunt paydalanıp atırǵan orın jasırıladı, hesh qashan óshirilmeydi.
    """
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_place')
    country = models.ForeignKey('geography.Country', on_delete=models.PROTECT, related_name='+')
    region = models.ForeignKey('geography.Region', on_delete=models.PROTECT, related_name='+')

    class Meta:
        db_table = 'partner_owner_places'


class CommissionRate(models.Model):
    """
    Sayt hár esaplanatuǵın bronnan mehmanxana iyesinen alatuǵın procent, `effective_from` niń birinshi
    kúninen baslap (hárdayım ay baslanıwı). Hár iye ushın hár ay bir qatar; aydıń kursı sol aydan keyin bolmaǵan eń sońǵı
    qatar, sol sebepli ózgeris aldınǵı aydı hesh qashan qayta jazbaydı hám qatarı joq iyede komissiya joq.
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
    "Bul iye usı aydıń komissiyasın tólegen", super admin yamasa staff admin tastıyıqlaǵan. Tastıyıqlawshınıń atı hám
    roli hám summalar usı jerge kóshiriledi, sol sebepli akkaunt atın ózgertse yamasa keyingi bronlar aydıń
    sanların ózgertse de jazba durıs qaladı.
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
