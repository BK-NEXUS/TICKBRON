"""
Logging configuration for TICKBRON Backend.

Provides structured logging with different handlers for development and production.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
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
                'handlers': ['console', 'error_file'],
                'level': 'ERROR',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            'tickbron': {
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console'],
            'level': log_level,
        }
    }
