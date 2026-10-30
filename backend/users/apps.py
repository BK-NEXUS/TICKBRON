from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'User Management'

    def ready(self):
        """
        Import signal handlers when the app is ready.
        """
        try:
            import users.signals  # noqa: F401  (connects the signal handlers)
        except ImportError:
            pass
