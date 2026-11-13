from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'User Management'

    def ready(self):
        """
        App tayın bolǵanda signal handler lerdi import etiw.
        """
        try:
            import users.signals  # noqa: F401  (connects the signal handlers)
        except ImportError:
            pass
