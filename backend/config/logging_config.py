"""
Logging configuration for TICKBRON Backend.

Provides structured logging with different handlers for development and production.
"""
import os
from django.conf import settings

def get_logging_config():
    """
    Get logging configuration based on environment.
    
    Returns a dict suitable for Django's LOGGING setting.
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO' if settings.DEBUG else 'WARNING')
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': log_format,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
                'level': log_level,
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(settings.BASE_DIR, 'logs', 'tickbron.log'),
                'maxBytes': 10 * 1024 * 1024,  # 10 MB
                'backupCount': 5,
                'formatter': 'verbose',
                'level': log_level,
            },
            # Telegram message for a security event worth acting on or any ERROR (see common/alerts.py)
            'alerts': {
                'class': 'common.alerts.AlertHandler',
                'level': 'WARNING',
            },
            # Security events (logins, lockouts, refused requests) are kept at INFO whatever LOG_LEVEL is
            'security_console': {
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
                'level': 'INFO',
            },
            'security_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(settings.BASE_DIR, 'logs', 'security.log'),
                'maxBytes': 10 * 1024 * 1024,  # 10 MB
                'backupCount': 10,
                'formatter': 'verbose',
                'level': 'INFO',
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(settings.BASE_DIR, 'logs', 'error.log'),
                'maxBytes': 10 * 1024 * 1024,  # 10 MB
                'backupCount': 5,
                'formatter': 'verbose',
                'level': 'ERROR',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': 'WARNING',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console', 'error_file', 'alerts'],
                'level': 'ERROR',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            'tickbron': {
                'handlers': ['console', 'file', 'alerts'],
                'level': log_level,
                'propagate': False,
            },
            'tickbron.security': {
                'handlers': ['security_console', 'security_file', 'alerts'],
                'level': 'INFO',
                'propagate': False,
            },
        },
        'root': {
            # Module loggers (getLogger(__name__): payments, bookings, users...) end up here
            'handlers': ['console', 'file', 'alerts'],
            'level': log_level,
        }
    }
