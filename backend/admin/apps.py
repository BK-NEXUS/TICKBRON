"""
Admin app configuration.
"""
from django.apps import AppConfig


class AdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin'
    verbose_name = 'Admin Management'
