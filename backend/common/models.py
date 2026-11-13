"""
TICKBRON ushın ulıwma model ler hám mixin ler

Bul modul barlıq TICKBRON app larında ortaq funkciyanı beretuǵın tiykarǵı model ler hám
mixin lerdi óz ishine aladı.
"""
from django.db import models


class TimeStampedModel(models.Model):
    """
    Jaratıw hám ózgertiw waqıt maydanların beretuǵın abstract tiykarǵı model.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):
    """
    Soft delete funkciyasın beretuǵın abstract tiykarǵı model.
    Jazbalar database den alıp taslanbastan óshirilgen dep belgilenedi.
    """
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self):
        """Jazbanı database den alıp taslamastan óshirilgen dep belgilew."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Soft-delete etilgen jazbanı qayta tiklew."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class ActiveModel(models.Model):
    """
    Aktiv/aktiv emes statusın beretuǵın abstract tiykarǵı model.
    """
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class BaseQuerySet(models.QuerySet):
    """
    Ulıwma filterlew metodları bar óz queryset i.
    """
    def active(self):
        """Tek aktiv jazbalardı qaytaradı."""
        return self.filter(is_active=True)

    def deleted(self):
        """Tek soft-delete etilgen jazbalardı qaytaradı."""
        return self.filter(is_deleted=True)

    def not_deleted(self):
        """Tek óshirilmegen jazbalardı qaytaradı."""
        return self.filter(is_deleted=False)


class BaseModel(TimeStampedModel, SoftDeleteModel, ActiveModel):
    """
    Waqıt belgisi, soft delete hám aktiv status funkciyaların birlestirgen tiykarǵı model.
    """
    objects = BaseQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ['-created_at']
