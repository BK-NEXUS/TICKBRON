"""
Celery Configuration for TICKBRON
"""

import os

try:
    from celery import Celery

    # Set the default Django settings module for the 'celery' program.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    app = Celery('tickbron')

    # Load configuration from Django settings
    app.config_from_object('django.conf:settings', namespace='CELERY')

    # Auto-discover tasks in all installed apps
    app.autodiscover_tasks()
except ImportError:
    # Celery not installed (e.g. a minimal environment): run without a worker app
    app = None
