from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'
    verbose_name = 'Common'
    
    def ready(self):
        """Import signal handlers when the app is ready."""
        try:
            import common.signals
        except ImportError:
            pass
