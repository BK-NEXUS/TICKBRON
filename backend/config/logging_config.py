"""
TICKBRON Backend ushın logging sazlaması.

Development hám production ushın túrli handler ler menen dúzilgen logging di usınadı.
"""
import os
from django.conf import settings


def get_logging_config():
    """
    Ortalıqqa qarap logging sazlamasın alıw.

    Django nıń LOGGING sazlaması ushın jaraytuǵın dict qaytaradı.
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
            # Háreket etiwge ılayıq qáwipsizlik waqıyası yamasa qálegen ERROR ushın Telegram xabarı (qarań common/alerts.py)
            'alerts': {
                'class': 'common.alerts.AlertHandler',
                'level': 'WARNING',
            },
            # Qáwipsizlik waqıyaları (kirisiw, lockout lar, qabıllanbaǵan sorawlar) LOG_LEVEL qanday bolsa da INFO da saqlanadı
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
            # Modul logger leri (getLogger(__name__): payments, bookings, users...) usı jerge túsedi
            'handlers': ['console', 'file', 'alerts'],
            'level': log_level,
        }
    }
