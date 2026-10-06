"""
TICKBRON Backend Settings

Django + Django REST Framework + PostgreSQL + Redis + Celery
"""

import os
import sys
from pathlib import Path
from decimal import Decimal

from celery.schedules import crontab
from dotenv import load_dotenv
from common.money import parse_percent
from .logging_config import get_logging_config

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Check if running in test mode
TESTING = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Validate SECRET_KEY in production (when DEBUG is False), but allow default for testing
if not DEBUG and SECRET_KEY == 'django-insecure-change-this-in-production' and not TESTING:
    raise ValueError('SECRET_KEY environment variable must be set in production')

# Validate ALLOWED_HOSTS in production (when DEBUG is False), but allow default for testing/development
_allowed_hosts = os.getenv('ALLOWED_HOSTS', '')
if not DEBUG and not _allowed_hosts and not TESTING:
    raise ValueError('ALLOWED_HOSTS environment variable must be set in production')
ALLOWED_HOSTS = _allowed_hosts.split(',') if _allowed_hosts else ['localhost', '127.0.0.1']


# Application definition

INSTALLED_APPS = [
    # 'django.contrib.admin',  # Removed - using custom admin_panel app instead
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # TICKBRON apps
    'common',
    'core',
    'users',
    'permissions',
    'properties',
    'bookings',
    'payments',
    'accounts',
    'partner',
    'admin_panel',
    'geography',
    'currency',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.middleware.SecurityHeadersMiddleware',
    'common.middleware.RequestLoggingMiddleware',
    'common.middleware.PerformanceMonitoringMiddleware',
]

ROOT_URLCONF = 'config.urls'

# Logging Configuration
LOGGING = get_logging_config()

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Database configuration - supports both SQLite (development) and PostgreSQL (production)
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
        'CONN_MAX_AGE': 60,  # Persistent connections for 60 seconds
        'OPTIONS': {},
    }
}

# PostgreSQL-specific settings when using PostgreSQL
if os.getenv('DB_ENGINE') == 'django.db.backends.postgresql':
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
        'sslmode': os.getenv('DB_SSLMODE', 'prefer'),
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        # Upper, lower, digit, special character, no common words
        'NAME': 'users.validators.StrongPasswordValidator',
        'OPTIONS': {
            'min_length': 12,
            'forbid_sequences': False,
        }
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

# R12: the date "today" for bookings, statistics and auto-completion (common.dates.business_today).
# TIME_ZONE stays UTC; hotels in other countries use this business date for now.
BUSINESS_TIME_ZONE = os.getenv('BUSINESS_TIME_ZONE', 'Asia/Tashkent')

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Security Settings
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000').split(',')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
# Cookies are https-only unless DEBUG is on (local http); override with the env vars
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Additional Security Headers
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True').lower() == 'true'
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'True').lower() == 'true'
SECURE_CONTENT_TYPE_NOSNIFF = os.getenv('SECURE_CONTENT_TYPE_NOSNIFF', 'True').lower() == 'true'
SECURE_BROWSER_XSS_FILTER = os.getenv('SECURE_BROWSER_XSS_FILTER', 'True').lower() == 'true'
X_FRAME_OPTIONS = os.getenv('X_FRAME_OPTIONS', 'DENY')

# CORS Settings
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Rate Limiting Settings
RATELIMIT_ENABLE = os.getenv('RATELIMIT_ENABLE', 'True').lower() == 'true'
RATELIMIT_USE_CACHE = 'default'

# Number of trusted reverse proxies in front of the app that append to
# X-Forwarded-For. 0 (default) ignores the header, since clients can forge it;
# set it to match the deployment (e.g. 1 behind a single nginx/load balancer).
NUM_PROXIES = int(os.getenv('NUM_PROXIES', '0'))

# Django REST Framework Settings
REST_FRAMEWORK = {
    'NUM_PROXIES': NUM_PROXIES,  # client IP for throttling; see common.request.get_client_ip
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'common.exception_handlers.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [] if TESTING else [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        # Per IP for anonymous visitors. One property page makes ~6 API calls, and
        # many users can share one IP (mobile carriers, offices), so this must not
        # be tight. Login, register, OTP and payment keep their own strict limits.
        'anon': os.getenv('THROTTLE_ANON_RATE', '2000/hour'),
        # Per logged-in user. The E2E crawl raises both rates (see frontend/playwright.config.ts)
        'user': os.getenv('THROTTLE_USER_RATE', '1000/hour'),
        # R12: hotels filing no-show reports (bookings.views_noshow.NoShowReportThrottle)
        'no_show_report': os.getenv('THROTTLE_NO_SHOW_REPORT_RATE', '20/hour'),
    },
}

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'TICKBRON API',
    'DESCRIPTION': 'TICKBRON API Documentation',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # Several models have a field named "status" with different choices
    'ENUM_NAME_OVERRIDES': {
        'BookingStatusEnum': 'bookings.models.Booking.STATUS_CHOICES',
        'PaymentTransactionStatusEnum': 'payments.models.PaymentTransaction.STATUS_CHOICES',
        'WebhookEventStatusEnum': 'payments.models.WebhookEvent.STATUS_CHOICES',
        'PropertyStatusEnum': 'properties.models.Property.STATUS_CHOICES',
        'ReviewStatusEnum': 'accounts.models.Review.STATUS_CHOICES',
    },
}

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_URL = os.getenv('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')

# Cache (throttling and rate-limit counters live here). Redis shares them
# across all workers; LocMem is per process and only suitable for local
# development. Defaults to Redis when DEBUG is off; tests always use LocMem.
USE_REDIS_CACHE = os.getenv('USE_REDIS_CACHE', str(not DEBUG)).lower() == 'true' and not TESTING
if USE_REDIS_CACHE:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'tickbron-local',
        }
    }

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
# R12: beat schedules are written in business time (Asia/Tashkent) whatever TIME_ZONE is.
# Production must run Celery beat, a worker and Redis (RELEASE_CHECKLIST).
CELERY_TIMEZONE = BUSINESS_TIME_ZONE

# Periodic tasks (run with: celery -A config beat -l info)
EXPIRED_BOOKINGS_INTERVAL_SECONDS = int(os.getenv('EXPIRED_BOOKINGS_INTERVAL_SECONDS', '60'))
CELERY_BEAT_SCHEDULE = {
    # Pending bookings expire after 15 minutes; release their inventory promptly
    'expire-pending-bookings': {
        'task': 'bookings.tasks.expire_pending_bookings',
        'schedule': EXPIRED_BOOKINGS_INTERVAL_SECONDS,
    },
    # CBU exchange rates at 09:00 and 18:00 Asia/Tashkent (CELERY_TIMEZONE)
    'fetch-exchange-rates': {
        'task': 'currency.tasks.fetch_exchange_rates',
        'schedule': crontab(hour='9,18', minute=0),
    },
    # R12: confirmed stays whose check-out date has passed become completed, 00:05 Asia/Tashkent
    'complete-finished-stays': {
        'task': 'bookings.tasks.complete_finished_stays',
        'schedule': crontab(hour=0, minute=5),
    },
}

# Exchange rates (R6). Thresholds come from the environment; see currency/cbu.py
FX_STALE_AFTER_DAYS = int(os.getenv('FX_STALE_AFTER_DAYS', '3'))
FX_MAX_CHANGE = Decimal(os.getenv('FX_MAX_CHANGE', '0.10'))      # reject jumps over 10 %
FX_MIN_RATE = Decimal(os.getenv('FX_MIN_RATE', '1000'))          # UZS per USD, sane range
FX_MAX_RATE = Decimal(os.getenv('FX_MAX_RATE', '100000'))
FX_FETCH_TIMEOUT = int(os.getenv('FX_FETCH_TIMEOUT', '10'))      # seconds

# R12 Status: CSV exports stop after this many rows (then a final "truncated" line)
CSV_EXPORT_MAX_ROWS = int(os.getenv('CSV_EXPORT_MAX_ROWS', '10000'))
# R12: hotels may report a no-show up to this many days after check-out (phase 3), so the
# Status "stayed" numbers of that window can still change
NO_SHOW_REPORT_WINDOW_DAYS = int(os.getenv('NO_SHOW_REPORT_WINDOW_DAYS', '7'))
# R12 phase 3: the share of the amount paid that goes back to the guest when staff approve a hotel's
# no-show report. A whole number 0-100 (startup fails otherwise). Every booking stores the value at
# creation (Booking.no_show_refund_percent); changing this never changes existing bookings.
NO_SHOW_REFUND_PERCENT = parse_percent('NO_SHOW_REFUND_PERCENT', os.getenv('NO_SHOW_REFUND_PERCENT'), default=50)
# R12 phase 3: a hotel is flagged in the staff queue when, over the last NO_SHOW_FLAG_DAYS days, it has at
# least NO_SHOW_FLAG_MIN_REPORTS reports AND its report rate is at least NO_SHOW_FLAG_FACTOR times the
# platform rate AND at least NO_SHOW_FLAG_MIN_RATE (so a near-zero average does not flag everyone)
NO_SHOW_FLAG_DAYS = int(os.getenv('NO_SHOW_FLAG_DAYS', '90'))
NO_SHOW_FLAG_MIN_REPORTS = int(os.getenv('NO_SHOW_FLAG_MIN_REPORTS', '5'))
NO_SHOW_FLAG_FACTOR = Decimal(os.getenv('NO_SHOW_FLAG_FACTOR', '3'))
NO_SHOW_FLAG_MIN_RATE = Decimal(os.getenv('NO_SHOW_FLAG_MIN_RATE', '0.10'))

# Database connection health check
DATABASE_HEALTH_CHECK_ENABLED = os.getenv('DATABASE_HEALTH_CHECK_ENABLED', 'True').lower() == 'true'
DATABASE_HEALTH_CHECK_INTERVAL = int(os.getenv('DATABASE_HEALTH_CHECK_INTERVAL', '60'))

# Payment Configuration
# Defaults to False: test mode confirms payments without a real provider.
PAYMENT_TEST_MODE = os.getenv('PAYMENT_TEST_MODE', 'False').lower() == 'true'

# Payment Provider Configuration (placeholders for production)
PAYME_MERCHANT_ID = os.getenv('PAYME_MERCHANT_ID', '')
PAYME_SECRET_KEY = os.getenv('PAYME_SECRET_KEY', '')
CLICK_SERVICE_ID = os.getenv('CLICK_SERVICE_ID', '')
CLICK_SECRET_KEY = os.getenv('CLICK_SECRET_KEY', '')
CLICK_MERCHANT_ID = os.getenv('CLICK_MERCHANT_ID', '')
VISA_API_KEY = os.getenv('VISA_API_KEY', '')
VISA_SECRET_KEY = os.getenv('VISA_SECRET_KEY', '')

# SMS Configuration
# Defaults to False: test mode returns the OTP code in the API response.
SMS_TEST_MODE = os.getenv('SMS_TEST_MODE', 'False').lower() == 'true'


# Production refuses to start on insecure settings (R4 security review).
# Local development (DEBUG=True) and the test run keep their defaults.
_PLACEHOLDER_SECRET_KEYS = {
    'django-insecure-change-this-in-production',
    'your-secret-key-here-change-in-production',
}


def _production_config_errors():
    errors = []
    if SMS_TEST_MODE:
        errors.append('SMS_TEST_MODE must be False when DEBUG is False (it returns OTP codes in API responses)')
    if PAYMENT_TEST_MODE:
        errors.append('PAYMENT_TEST_MODE must be False when DEBUG is False (payments would not reach a provider)')
    if (SECRET_KEY in _PLACEHOLDER_SECRET_KEYS or SECRET_KEY.startswith('django-insecure-')
            or len(SECRET_KEY) < 50):
        errors.append('SECRET_KEY must be a random value of at least 50 characters, not a placeholder')
    if '*' in ALLOWED_HOSTS:
        errors.append("ALLOWED_HOSTS must list the real host names, not '*'")
    for name in ('CORS_ALLOWED_ORIGINS', 'CSRF_TRUSTED_ORIGINS'):
        raw = os.getenv(name, '').strip()
        if not raw:
            errors.append(f'{name} must be set (comma-separated https:// origins)')
        elif any(not origin.strip().startswith('https://') for origin in raw.split(',')):
            errors.append(f'{name} may only contain https:// origins')
    return errors


if not DEBUG and not TESTING:
    _errors = _production_config_errors()
    if _errors:
        raise ValueError('Insecure production settings:\n- ' + '\n- '.join(_errors))
