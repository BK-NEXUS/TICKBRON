"""
accounts app ınıń sazlaması (AppConfig).
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    accounts app ınıń sazlaması.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Accounts'
