"""
Geografiya sózligi: Country > Region (regiondan tómen qala yamasa tuman joq).

Atlar ózbek (Latin), rus hám inglizshe saqlanadı; frontend tildi
tańlaydı. Paydalanılıp atırǵan qatarlar hesh qashan óshirilmeydi (PROTECT): olardı is_active=False penen jasırıń.
"""
import os
import uuid

from django.db import models
from django.utils.text import slugify

from common.models import BaseModel

LANGUAGES = ('uz', 'ru', 'en')


def _random_image_path(folder, filename):
    """Saqlanǵan súwret atları tosınarlıq: jol ashıq hám boljawǵa bolmaytuǵın bolıwı kerek."""
    return f'geography/{folder}/{uuid.uuid4().hex}{os.path.splitext(filename)[1].lower()}'


def country_image_path(instance, filename):
    return _random_image_path('countries', filename)


def region_image_path(instance, filename):
    return _random_image_path('regions', filename)


class GeoName(BaseModel):
    """Ortaq maydanlar: úsh at, aktiv flag (BaseModel den) hám tártip nomeri."""
    name_uz = models.CharField(max_length=150)
    name_ru = models.CharField(max_length=150)
    name_en = models.CharField(max_length=150)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True

    def name(self, language='en'):
        """`language` degi at (uz, ru, en); belgisiz yamasa bos bolsa inglizsha."""
        if language in LANGUAGES:
            value = getattr(self, f'name_{language}')
            if value:
                return value
        return self.name_en

    def __str__(self):
        return self.name_en


class Country(GeoName):
    code = models.CharField(max_length=2, unique=True, help_text='ISO 3166-1 alpha-2, e.g. UZ')
    currency = models.CharField(max_length=3, help_text='ISO 4217, e.g. UZS')
    image = models.ImageField(upload_to=country_image_path, null=True, blank=True)

    class Meta:
        db_table = 'geo_countries'
        ordering = ['sort_order', 'name_en']
        verbose_name_plural = 'Countries'

    def save(self, *args, **kwargs):
        self.code = (self.code or '').strip().upper()
        self.currency = (self.currency or '').strip().upper()
        super().save(*args, **kwargs)


class Region(GeoName):
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='regions')
    image = models.ImageField(upload_to=region_image_path, null=True, blank=True)
    # Turaqlı kilt (mısalı "uz-khorezm-region"): bir márte belgilenedi, at ózgergende hesh qashan ózgermeydi
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    class Meta:
        db_table = 'geo_regions'
        ordering = ['sort_order', 'name_en']
        constraints = [
            models.UniqueConstraint(fields=['country', 'name_en'], name='geo_region_unique_name_en'),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.country.code}-{self.name_en}')
        super().save(*args, **kwargs)
