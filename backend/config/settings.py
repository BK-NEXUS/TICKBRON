"""
TICKBRON Backend Settings

Django + Django REST Framework + PostgreSQL + Redis + Celery
"""

import base64
import ipaddress
import os
import re
import sys
from pathlib import Path
from decimal import Decimal

from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
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


def _env_list(raw):
    """Comma-separated env value -> list, whitespace and empty entries dropped ("a.com, b.com" is two hosts)."""
    return [item.strip() for item in raw.split(',') if item.strip()]


ALLOWED_HOSTS = _env_list(_allowed_hosts) or ['localhost', '127.0.0.1']


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
    'promotions',
    'chat',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'common.middleware.RequestBodyLimitMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # The site sends Accept-Language (uz, ru, en); validation errors come back in that language
    'common.middleware.RequestLanguageMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # An administrator without two-step sign-in can only set it up (users/two_factor.py)
    'users.middleware.TwoFactorSetupMiddleware',
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

# PostgreSQL only: SQLite has no row locks, so the double-booking protection would silently stop
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'tickbron'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,  # Persistent connections for 60 seconds
        'CONN_HEALTH_CHECKS': True,  # a connection the database closed (restart) is replaced, not served as a 500
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': os.getenv('DB_SSLMODE', 'prefer'),
        },
    }
}


# Each developer session (or Claude session) sets its own TICKBRON_TEST_DB_SUFFIX so two pytest
# runs on one PostgreSQL server never share a test database (xdist adds _gw0, _gw1, ... to it)
TEST_DB_SUFFIX = os.getenv('TICKBRON_TEST_DB_SUFFIX', '')
if TEST_DB_SUFFIX:
    if not re.fullmatch(r'[A-Za-z0-9_]{1,30}', TEST_DB_SUFFIX):
        raise ImproperlyConfigured('TICKBRON_TEST_DB_SUFFIX may only contain letters, digits and _ (max 30)')
    DATABASES['default']['TEST'] = {'NAME': f"test_{DATABASES['default']['NAME']}_{TEST_DB_SUFFIX}"}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
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
        # Letter, digit, special character, no common words
        'NAME': 'users.validators.StrongPasswordValidator',
        'OPTIONS': {
            'min_length': 8,
            'forbid_sequences': False,
        }
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
LANGUAGES = [('en', 'English'), ('ru', 'Русский'), ('uz', 'Oʻzbekcha')]
LOCALE_PATHS = [BASE_DIR / 'locale']

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
CSRF_TRUSTED_ORIGINS = _env_list(os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000'))
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
# Behind a TLS-terminating proxy (nginx) Django only sees http. With this on it trusts the
# proxy's X-Forwarded-Proto, so request.is_secure(), the https redirect and HSTS work and the
# redirect does not loop. Turn it on only when the proxy always overwrites that header.
SECURE_PROXY_SSL_HEADER = (
    ('HTTP_X_FORWARDED_PROTO', 'https')
    if os.getenv('USE_X_FORWARDED_PROTO', 'False').lower() == 'true' else None
)
# Cookies are https-only unless DEBUG is on (local http); override with the env vars
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
# A stolen session cookie stops working after a week (Django's default is two)
SESSION_COOKIE_AGE = int(os.getenv('SESSION_COOKIE_AGE', str(7 * 24 * 3600)))

# Additional Security Headers
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True').lower() == 'true'
# Preload is hard to undo (browsers ship the list), so it is an explicit owner decision
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'False').lower() == 'true'
SILENCED_SYSTEM_CHECKS = ['security.W021']  # W021 asks for preload: documented choice above
SECURE_CONTENT_TYPE_NOSNIFF = os.getenv('SECURE_CONTENT_TYPE_NOSNIFF', 'True').lower() == 'true'
X_FRAME_OPTIONS = os.getenv('X_FRAME_OPTIONS', 'DENY')

# Two-step sign-in (users/two_factor.py): administrators and staff must have it. TWO_FACTOR_KEY seals the
# authenticator secrets in the database; development and tests derive a key from SECRET_KEY instead.
# Off by default until the site's sign-in screen has the code step (planned: on in production by default)
TWO_FACTOR_REQUIRED_FOR_ADMINS = os.getenv('TWO_FACTOR_REQUIRED_FOR_ADMINS', 'False').lower() == 'true'
TWO_FACTOR_KEY = os.getenv('TWO_FACTOR_KEY', '')

# CORS Settings
CORS_ALLOWED_ORIGINS = _env_list(os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000'))
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

# Number of trusted reverse proxies in front of the app that append to
# X-Forwarded-For. 0 (default) ignores the header, since clients can forge it;
# set it to match the deployment (e.g. 1 behind a single nginx/load balancer).
def _read_num_proxies():
    raw = os.getenv('NUM_PROXIES')
    if raw is None:
        return 0, None
    try:
        count = int(raw)
    except ValueError:
        return 0, f'NUM_PROXIES must be a whole number, got {raw!r}'
    return (count, None) if count >= 0 else (0, 'NUM_PROXIES must not be negative')


NUM_PROXIES, _NUM_PROXIES_ERROR = _read_num_proxies()

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
    # The browsable API (HTML forms for every endpoint) is a development tool only
    'DEFAULT_RENDERER_CLASSES': (
        ['rest_framework.renderers.JSONRenderer', 'rest_framework.renderers.BrowsableAPIRenderer'] if DEBUG
        else ['rest_framework.renderers.JSONRenderer']
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'common.exception_handlers.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [] if TESTING else [
        'common.throttling.BlockAnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        # Per IP for anonymous visitors. One property page makes ~6 API calls, and
        # many users can share one IP (mobile carriers, offices), so this must not
        # be tight. Login, register and OTP keep their own strict limits.
        'anon': os.getenv('THROTTLE_ANON_RATE', '2000/hour'),
        # Per logged-in user. The E2E crawl raises both rates (see frontend/playwright.config.ts)
        'user': os.getenv('THROTTLE_USER_RATE', '1000/hour'),
        'booking_create': os.getenv('THROTTLE_BOOKING_CREATE_RATE', '30/hour'),
        # R12: hotels filing no-show reports (bookings.views_noshow.NoShowReportThrottle)
        'no_show_report': os.getenv('THROTTLE_NO_SHOW_REPORT_RATE', '20/hour'),
        # Support chat: writing, and reading (the page polls while the chat is open)
        'chat_send': os.getenv('THROTTLE_CHAT_SEND_RATE', '20/min'),
        'chat_poll': os.getenv('THROTTLE_CHAT_POLL_RATE', '90/min'),
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
        'PropertyStatusEnum': 'properties.models.Property.STATUS_CHOICES',
        'ReviewStatusEnum': 'accounts.models.Review.STATUS_CHOICES',
        'NoShowReportStatusEnum': 'bookings.models.NoShowReport.STATUS_CHOICES',
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
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                # A dead Redis must fail fast; without timeouts every worker hangs on the OS TCP timeout
                'SOCKET_CONNECT_TIMEOUT': 2,
                'SOCKET_TIMEOUT': 2,
            },
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'tickbron-local',
        }
    }

# R16: when True (the default), a rate plan must carry the owner's price in every supported currency (create and
# every edit); the owner decided this on 2026-10-19 (see .ai/PLAN_R16_MULTI_CURRENCY.md).
RATE_PLAN_PRICES_REQUIRED = os.getenv('RATE_PLAN_PRICES_REQUIRED', 'True').lower() == 'true'

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
# Local development without a worker: run tasks (password reset e-mails, alerts) inside the request
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'False').lower() == 'true'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
# R12: beat schedules are written in business time (Asia/Tashkent) whatever TIME_ZONE is.
# Production must run Celery beat, a worker and Redis (RELEASE_CHECKLIST).
CELERY_TIMEZONE = BUSINESS_TIME_ZONE

# E-mail (password reset links). Local development prints the mail to the console; production sends it
# through SMTP and must say where the site lives, because the link points to the frontend.
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'TICKBRON <no-reply@tickbron.com>')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
# Where the team hears of a new chat message (empty = the team is not mailed; the admin tab still shows the badge)
SUPPORT_NOTIFY_EMAIL = os.getenv('SUPPORT_NOTIFY_EMAIL', '')
PASSWORD_RESET_TIMEOUT = 60 * 60  # a reset link works for one hour

# Alerts to a Telegram chat (common/alerts.py). Both empty = alerts off. Create the bot with
# @BotFather, add it to the chat and take the chat id from the getUpdates call.
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_ALERT_CHAT_ID = os.getenv('TELEGRAM_ALERT_CHAT_ID', '')

# Periodic tasks (run with: celery -A config beat -l info)
EXPIRED_BOOKINGS_INTERVAL_SECONDS = int(os.getenv('EXPIRED_BOOKINGS_INTERVAL_SECONDS', '60'))
CELERY_BEAT_SCHEDULE = {
    # Pending bookings expire after 15 minutes; release their inventory promptly
    'expire-pending-bookings': {
        'task': 'bookings.tasks.expire_pending_bookings',
        'schedule': EXPIRED_BOOKINGS_INTERVAL_SECONDS,
    },
    # A confirmed booking whose guest has not arrived ARRIVAL_GRACE_HOURS after the given time is cancelled
    'cancel-unarrived-bookings': {
        'task': 'bookings.tasks.cancel_unarrived_bookings',
        'schedule': crontab(minute='*/10'),
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
    # Monthly ad renewal: ask "did the hotel pay for the next month?", remove ads not renewed in time, 00:05 Asia/Tashkent
    # (before the 00:10 tidy below, which leaves an ad with an open question running)
    'run-ad-renewals': {
        'task': 'promotions.tasks.run_ad_renewals',
        'schedule': crontab(hour=0, minute=5),
    },
    # R10: expired hotel promotions end, paid ones that started become active, 00:10 Asia/Tashkent
    'end-expired-promotions': {
        'task': 'promotions.tasks.end_expired_promotions',
        'schedule': crontab(hour=0, minute=10),
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
# Cash bookings: hours the hotel waits after the arrival time the guest gave before the booking is cancelled
ARRIVAL_GRACE_HOURS = int(os.getenv('ARRIVAL_GRACE_HOURS', '2'))
# R12 phase 3: a hotel is flagged in the staff queue when, over the last NO_SHOW_FLAG_DAYS days, it has at
# least NO_SHOW_FLAG_MIN_REPORTS reports AND its report rate is at least NO_SHOW_FLAG_FACTOR times the
# platform rate AND at least NO_SHOW_FLAG_MIN_RATE (so a near-zero average does not flag everyone)
NO_SHOW_FLAG_DAYS = int(os.getenv('NO_SHOW_FLAG_DAYS', '90'))
NO_SHOW_FLAG_MIN_REPORTS = int(os.getenv('NO_SHOW_FLAG_MIN_REPORTS', '5'))
NO_SHOW_FLAG_FACTOR = Decimal(os.getenv('NO_SHOW_FLAG_FACTOR', '3'))
NO_SHOW_FLAG_MIN_RATE = Decimal(os.getenv('NO_SHOW_FLAG_MIN_RATE', '0.10'))

# Database connection health check

# Production refuses to start on insecure settings (R4 security review).
# Local development (DEBUG=True) and the test run keep their defaults.
_PLACEHOLDER_SECRET_KEYS = {
    'django-insecure-change-this-in-production',
    'your-secret-key-here-change-in-production',
}


def _is_fernet_key(value):
    try:
        return len(base64.urlsafe_b64decode(value)) == 32
    except ValueError:
        return False


def _production_config_errors():
    errors = []
    if (SECRET_KEY in _PLACEHOLDER_SECRET_KEYS or SECRET_KEY.startswith('django-insecure-')
            or len(SECRET_KEY) < 50):
        errors.append('SECRET_KEY must be a random value of at least 50 characters, not a placeholder')
    if '*' in ALLOWED_HOSTS:
        errors.append("ALLOWED_HOSTS must list the real host names, not '*'")
    # N-3: unset means "no proxy", and behind nginx every visitor then shares one IP, so the login
    # throttle, the account lockout and the promotion counters collapse into one bucket
    if _NUM_PROXIES_ERROR:
        errors.append(_NUM_PROXIES_ERROR)
    elif os.getenv('NUM_PROXIES') is None:
        errors.append('NUM_PROXIES must be set (0 = no reverse proxy, 1 = one nginx/load balancer in front)')
    # N-6: https must be enforced, and a TLS-terminating proxy needs its header trusted
    if not SECURE_SSL_REDIRECT:
        errors.append('SECURE_SSL_REDIRECT must be True when DEBUG is False')
    if NUM_PROXIES > 0 and SECURE_PROXY_SSL_HEADER is None:
        errors.append('USE_X_FORWARDED_PROTO must be True behind a reverse proxy (otherwise the https redirect loops)')
    # Password reset: the e-mailed link points to the frontend and needs a mail server to be sent
    if not FRONTEND_URL.startswith('https://'):
        errors.append('FRONTEND_URL must be the https:// address of the site (password reset links point to it)')
    if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend' and not EMAIL_HOST:
        errors.append('EMAIL_HOST must be set (password reset e-mails cannot be sent without a mail server)')
    if TWO_FACTOR_REQUIRED_FOR_ADMINS and not _is_fernet_key(TWO_FACTOR_KEY):
        errors.append('TWO_FACTOR_KEY must be set to a Fernet key (see deploy/env.production.example)')
    # N-19
    if not SESSION_COOKIE_SECURE:
        errors.append('SESSION_COOKIE_SECURE must be True when DEBUG is False')
    if not CSRF_COOKIE_SECURE:
        errors.append('CSRF_COOKIE_SECURE must be True when DEBUG is False')
    if not USE_REDIS_CACHE:
        errors.append('USE_REDIS_CACHE must be True when DEBUG is False (lockouts and throttles need a shared cache)')
    # docker-compose.yml names its database container `db` and reaches it over Docker's own network on the
    # same machine: DB_NETWORK_IS_PRIVATE=True says so, and only a bare service name (no dot, no IP) counts
    db_host = os.getenv('DB_HOST', '')
    db_on_private_network = (os.getenv('DB_NETWORK_IS_PRIVATE', 'False').lower() == 'true'
                             and '.' not in db_host and ':' not in db_host)
    if (db_host not in ('', 'localhost', '127.0.0.1', '::1') and not db_on_private_network
            and os.getenv('DB_SSLMODE', 'prefer') in ('disable', 'allow', 'prefer')):
        errors.append('DB_SSLMODE must be require, verify-ca or verify-full for a remote database')
    for name in ('CORS_ALLOWED_ORIGINS', 'CSRF_TRUSTED_ORIGINS'):
        raw = os.getenv(name, '').strip()
        if not raw:
            errors.append(f'{name} must be set (comma-separated https:// origins)')
        elif any(not origin.strip().startswith('https://') for origin in raw.split(',')):
            errors.append(f'{name} may only contain https:// origins')
    return errors


def _is_local_host(host):
    """localhost, a *.localhost / *.local name or an IP address: places a developer's own machine can be."""
    host = host.strip('[]')
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return host == 'localhost' or host.endswith(('.localhost', '.local'))


if DEBUG and not TESTING and not all(_is_local_host(host) for host in ALLOWED_HOSTS):
    # DEBUG shows stack traces, opens the API docs and skips every check below: never on a public domain
    raise ValueError('DEBUG must be False when ALLOWED_HOSTS lists a public host name')

if not DEBUG and not TESTING:
    _errors = _production_config_errors()
    if _errors:
        raise ValueError('Insecure production settings:\n- ' + '\n- '.join(_errors))
