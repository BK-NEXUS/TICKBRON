from django.apps import AppConfig


class PermissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'permissions'
    verbose_name = 'Permissions & Roles'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        """
        try:
            import permissions.signals
        except ImportError:
            pass
