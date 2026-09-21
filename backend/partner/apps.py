"""
Partner app configuration.
"""
from django.apps import AppConfig


class PartnerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'partner'
    verbose_name = 'Partner Management'
