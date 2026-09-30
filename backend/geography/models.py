"""
Geography dictionary: Country > Region > City.

Names are stored in Uzbek (Latin), Russian and English; the frontend picks the
language. Rows in use are never deleted (PROTECT): hide them with is_active=False.
"""
from django.db import models
from django.utils.text import slugify

from common.models import BaseModel

LANGUAGES = ('uz', 'ru', 'en')


class GeoName(BaseModel):
    """Shared fields: three names, active flag (from BaseModel) and a sort order."""
    name_uz = models.CharField(max_length=150)
    name_ru = models.CharField(max_length=150)
    name_en = models.CharField(max_length=150)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True

    def name(self, language='en'):
        """The name in `language` (uz, ru, en); English when unknown or empty."""
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
    # Stable key (e.g. "uz-khorezm-region"): set once, never changed by a rename
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


class City(GeoName):
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='cities')
    # Stable key (e.g. "uz-khorezm-region-khiva"): set once, never changed by a rename
    slug = models.SlugField(max_length=250, unique=True, blank=True)

    class Meta:
        db_table = 'geo_cities'
        ordering = ['sort_order', 'name_en']
        verbose_name_plural = 'Cities'
        constraints = [
            models.UniqueConstraint(fields=['region', 'name_en'], name='geo_city_unique_name_en'),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.region.slug}-{self.name_en}')
        super().save(*args, **kwargs)
