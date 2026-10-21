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
