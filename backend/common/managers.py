"""
TICKBRON model leri ushın óz manager leri.

Bul modul qosımsha query múmkinshiliklerin beretuǵın óz manager lerin óz ishine aladı.
"""
from django.db import models


class SoftDeleteManager(models.Manager):
    """
    Ádetde soft-delete etilgen jazbalardı shıǵarıp taslaytuǵın manager.
    """
    def get_queryset(self):
        """Soft-delete etilgen jazbalarsız queryset qaytaradı."""
        return super().get_queryset().filter(is_deleted=False)
