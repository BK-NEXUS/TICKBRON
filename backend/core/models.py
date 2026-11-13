"""
TICKBRON ushın core model leri.

Bul modul TICKBRON sisteması ushın tiykarǵı funkciyanı beretuǵın
tiykarǵı app model lerin óz ishine aladı.
"""
from django.db import models
from common.models import BaseModel


class SystemSettings(BaseModel):
    """
    Sistema dárejesindegi sazlamalar hám konfiguraciya.
    """
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value}"
