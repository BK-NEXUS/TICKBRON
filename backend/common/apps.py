from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'
    verbose_name = 'Common'

    def ready(self):
        """App tayın bolǵanda signal handler lerdi import etiw."""
        try:
            import common.signals  # noqa: F401  (connects the signal handlers)
        except ImportError:
            pass
