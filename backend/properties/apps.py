from django.apps import AppConfig


class PropertiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'properties'

    def ready(self):
        """App tayın bolǵanda signal handler lerdi import etiw."""
        import properties.signals  # noqa: F401  (connects the signal handlers)
