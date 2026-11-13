"""
TICKBRON Backend sazlamaları

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

# Environment ózgeriwshilerin júklew
load_dotenv()

# Proekt ishindegi jollardı bılay qurıń: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Test rejiminde isleytuǵının tekseriw
TESTING = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST')

if TESTING:
    # Testler parollardı tez algoritm menen hash laydı; production Django niń ádetdegisin (PBKDF2) saqlaydı.
    PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    # Programmistiń .env i (mısalı .env.dev.example) testler ádetdegi dep tastıyıqlaytuǵın mánislerdi ózgertpewi kerek.
    for _name in (
        'THROTTLE_ANON_RATE', 'THROTTLE_USER_RATE', 'THROTTLE_BOOKING_CREATE_RATE',
        'THROTTLE_NO_SHOW_REPORT_RATE', 'THROTTLE_CHAT_SEND_RATE', 'THROTTLE_CHAT_POLL_RATE',
        'THROTTLE_SEARCH_RATE', 'THROTTLE_PROMOTION_PUBLIC_RATE', 'THROTTLE_LOGIN_RATE', 'THROTTLE_REGISTER_RATE',
        'CELERY_TASK_ALWAYS_EAGER',
    ):
        os.environ.pop(_name, None)

# QÁWIPSIZLIK ESKERTIWI: production ta paydalanılatuǵın secret key di jasırın saqlań!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# QÁWIPSIZLIK ESKERTIWI: production ta debug ti qosıp islemeń!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Production ta (DEBUG False bolǵanda) SECRET_KEY di tekseriw, biraq testlew ushın ádetdegige ruxsat beriw
if not DEBUG and SECRET_KEY == 'django-insecure-change-this-in-production' and not TESTING:
    raise ValueError('SECRET_KEY environment variable must be set in production')

# Production ta (DEBUG False bolǵanda) ALLOWED_HOSTS ti tekseriw, biraq testlew/development ushın ádetdegige ruxsat beriw
_allowed_hosts = os.getenv('ALLOWED_HOSTS', '')
if not DEBUG and not _allowed_hosts and not TESTING:
    raise ValueError('ALLOWED_HOSTS environment variable must be set in production')


def _env_list(raw):
    """Útir menen ajıratılǵan env mánisi -> dizim, bos orınlar hám bos jazbalar taslanadı ("a.com, b.com" eki host)."""
    return [item.strip() for item in raw.split(',') if item.strip()]


ALLOWED_HOSTS = _env_list(_allowed_hosts) or ['localhost', '127.0.0.1']


# Application anıqlaması

INSTALLED_APPS = [
    # 'django.contrib.admin',  # Alıp taslandı - ornına óz admin_panel app ı paydalanıladı
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # TICKBRON app ları
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

    # Úshinshi tárep app ları
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'common.middleware.RequestBodyLimitMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    # CorsMiddleware ten keyin: onıń 400 i CORS header lerin alıp júriwi kerek, bolmasa brauzer 400 ornına CORS qátesin
    # kórsetedi
    'common.middleware.RejectNullCharactersMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Sayt Accept-Language (uz, ru, en) jiberedi; validation qátelikleri sol tilde qaytadı
    'common.middleware.RequestLanguageMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Eki basqıshlı kirisiwi joq administrator tek onı sazlay aladı (users/two_factor.py)
    'users.middleware.TwoFactorSetupMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.middleware.SecurityHeadersMiddleware',
    'common.middleware.RequestLoggingMiddleware',
    'common.middleware.PerformanceMonitoringMiddleware',
]

ROOT_URLCONF = 'config.urls'

# Logging sazlaması
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

# Tek PostgreSQL: SQLite te qatar qulıpları joq, sol sebepli qos bronlawdan qorǵanıs ún-túnsiz toqtap qalar edi
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'tickbron'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,  # 60 sekund dawamlı ulanıwlar
        'CONN_HEALTH_CHECKS': True,  # Database jawıp taslaǵan ulanıw (qayta iske túsiriw) 500 retinde emes, almastırıladı
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': os.getenv('DB_SSLMODE', 'prefer'),
        },
    }
}


# Hár programmist sessiyası (yamasa Claude sessiyası) óziniń TICKBRON_TEST_DB_SUFFIX in belgileydi, sonda bir
# PostgreSQL serverde eki pytest isleniwi hesh qashan bir test database di bólispeydi (xdist oǵan _gw0, _gw1, ... qosadı)
TEST_DB_SUFFIX = os.getenv('TICKBRON_TEST_DB_SUFFIX', '')
if TEST_DB_SUFFIX:
    if not re.fullmatch(r'[A-Za-z0-9_]{1,30}', TEST_DB_SUFFIX):
        raise ImproperlyConfigured('TICKBRON_TEST_DB_SUFFIX may only contain letters, digits and _ (max 30)')
    DATABASES['default']['TEST'] = {'NAME': f"test_{DATABASES['default']['NAME']}_{TEST_DB_SUFFIX}"}


# Parol tekseriwi
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
        # Háripti, sandı, arnawlı belgi, ápiwayı sózler joq
        'NAME': 'users.validators.StrongPasswordValidator',
        'OPTIONS': {
            'min_length': 8,
            'forbid_sequences': False,
        }
    },
]


# Xalıqaralastırıw (Internationalization)
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
LANGUAGES = [('en', 'English'), ('ru', 'Русский'), ('uz', 'Oʻzbekcha')]
LOCALE_PATHS = [BASE_DIR / 'locale']

TIME_ZONE = 'UTC'

# R12: bronlar, statistika hám avtomat juwmaqlaw ushın "búgin" sanası (common.dates.business_today).
# TIME_ZONE UTC bolıp qaladı; basqa mámleketlerdegi mehmanxanalar házirshe usı is sanasın paydalanadı.
BUSINESS_TIME_ZONE = os.getenv('BUSINESS_TIME_ZONE', 'Asia/Tashkent')

USE_I18N = True

USE_TZ = True


# Statik fayllar (CSS, JavaScript, súwretler)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media fayllar
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Ádetdegi primary key maydan túri
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Óz User modeli
AUTH_USER_MODEL = 'users.User'

# Qáwipsizlik sazlamaları
CSRF_TRUSTED_ORIGINS = _env_list(os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000'))
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
# TLS di tamamlaytuǵın proxy (nginx) artında Django tek http kóredi. Bul qosılǵanda ol
# proxy diń X-Forwarded-Proto sına isenedi, sol sebepli request.is_secure(), https redirect hám HSTS isleydi
# hám redirect aylanıp qalmaydı. Tek proxy sol header di hárdayım qayta jazǵanda qosıń.
SECURE_PROXY_SSL_HEADER = (
    ('HTTP_X_FORWARDED_PROTO', 'https')
    if os.getenv('USE_X_FORWARDED_PROTO', 'False').lower() == 'true' else None
)
# Cookie ler DEBUG qosılmaǵansha (jergilikli http) tek https; env ózgeriwshileri menen ózgertiń
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
# Urlanǵan session cookie bir háptedan keyin islewdi toqtatadı (Django tiń ádetdegisi eki)
SESSION_COOKIE_AGE = int(os.getenv('SESSION_COOKIE_AGE', str(7 * 24 * 3600)))

# Qosımsha qáwipsizlik header leri
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))  # 1 jıl
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True').lower() == 'true'
# Preload tı qaytarıw qıyın (brauzerler dizimdi jetkizedi), sol sebepli ol iyeniń anıq qararı
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'False').lower() == 'true'
SILENCED_SYSTEM_CHECKS = ['security.W021']  # W021 preload sorayıdı: joqarıda hújjetlestirilgen tańlaw
SECURE_CONTENT_TYPE_NOSNIFF = os.getenv('SECURE_CONTENT_TYPE_NOSNIFF', 'True').lower() == 'true'
X_FRAME_OPTIONS = os.getenv('X_FRAME_OPTIONS', 'DENY')

# Eki basqıshlı kirisiw (users/two_factor.py): administratorlar hám staff ta bolıwı shárt. TWO_FACTOR_KEY database degi
# authenticator sırların shifrlaydı; development hám testler onıń ornına SECRET_KEY ten kilt shıǵaradı.
TWO_FACTOR_REQUIRED_FOR_ADMINS = os.getenv('TWO_FACTOR_REQUIRED_FOR_ADMINS', str(not DEBUG and not TESTING)).lower() == 'true'
TWO_FACTOR_KEY = os.getenv('TWO_FACTOR_KEY', '')

# CORS sazlamaları
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

# Ilova aldındaǵı X-Forwarded-For ge qosatuǵın isenimli reverse proxy ler sanı.
# 0 (ádetde) header di itibarǵa almaydı, sebebi klientler onı jalǵan jasay aladı;
# onı deployment ke sáykes qoyıń (mısalı bir nginx/load balancer artında 1).


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

# Django REST Framework sazlamaları
REST_FRAMEWORK = {
    'NUM_PROXIES': NUM_PROXIES,  # throttling ushın klient IP si; qarań common.request.get_client_ip
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Browsable API (hár endpoint ushın HTML formalar) tek development quralı
    'DEFAULT_RENDERER_CLASSES': (
        ['rest_framework.renderers.JSONRenderer', 'rest_framework.renderers.BrowsableAPIRenderer'] if DEBUG
        else ['rest_framework.renderers.JSONRenderer']
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'common.exception_handlers.custom_exception_handler',
    # SafeJSONParser júda tereń oralǵan JSON ǵa 400 menen juwap beredi (ádettegi parser RecursionError dıń 500 bolıwına jol
    # qoyadı)
    'DEFAULT_PARSER_CLASSES': [
        'common.parsers.SafeJSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_THROTTLE_CLASSES': [] if TESTING else [
        'common.throttling.BlockAnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        # Anonim kelwshiler ushın IP boyınsha. Bir mehmanxana beti ~6 API shaqırıwın isleydi, hám
        # kóp paydalanıwshı bir IP ni bólisiwi múmkin (mobil operatorlar, ofisler), sol sebepli bul qattı bolmawı
        # kerek. Login, register hám OTP óz qattı limitlerin saqlaydı.
        'anon': os.getenv('THROTTLE_ANON_RATE', '2000/hour'),
        # Kirgen paydalanıwshı boyınsha. E2E crawl eki dárejeni de kóteredi (qarań frontend/playwright.config.ts)
        'user': os.getenv('THROTTLE_USER_RATE', '1000/hour'),
        'booking_create': os.getenv('THROTTLE_BOOKING_CREATE_RATE', '30/hour'),
        # R12: no-show esabatı jiberiwshi mehmanxanalar (bookings.views_noshow.NoShowReportThrottle)
        'no_show_report': os.getenv('THROTTLE_NO_SHOW_REPORT_RATE', '20/hour'),
        # Qollap-quwatlaw chatı: jazıw hám oqıw (chat ashıq waqıtta bet polling isleydi)
        'chat_send': os.getenv('THROTTLE_CHAT_SEND_RATE', '20/min'),
        'chat_poll': os.getenv('THROTTLE_CHAT_POLL_RATE', '90/min'),
    },
}

# API hújjetlestiriw
SPECTACULAR_SETTINGS = {
    'TITLE': 'TICKBRON API',
    'DESCRIPTION': 'TICKBRON API Documentation',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # Kóp model de "status" atlı, túrli tańlawlı maydan bar
    'ENUM_NAME_OVERRIDES': {
        'BookingStatusEnum': 'bookings.models.Booking.STATUS_CHOICES',
        'PropertyStatusEnum': 'properties.models.Property.STATUS_CHOICES',
        'ReviewStatusEnum': 'accounts.models.Review.STATUS_CHOICES',
        'NoShowReportStatusEnum': 'bookings.models.NoShowReport.STATUS_CHOICES',
    },
}

# Redis sazlaması
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_URL = os.getenv('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')

# Kesh (throttling hám rate-limit sanaǵıshları usı jerde turadı). Redis olardı barlıq
# worker ler arasında bóliskenlestiredi; LocMem hár process ushın bólek hám tek jergilikli
# development ke jaraydı. DEBUG óshirilgende ádetde Redis; testler hárdayım LocMem paydalanadı.
USE_REDIS_CACHE = os.getenv('USE_REDIS_CACHE', str(not DEBUG)).lower() == 'true' and not TESTING
if USE_REDIS_CACHE:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                # Óship qalǵan Redis tez qátelesiwi kerek; timeout lar bolmasa hár worker OS TCP timeout ında qatıp qaladı
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

# Hár kelwshi mánzili ushın izlew endpoint leriniń limiti (properties.views.SearchRateThrottle)
SEARCH_THROTTLE_RATE = os.getenv('THROTTLE_SEARCH_RATE', '100/min')
# Hár kelwshi mánzili ushın ashıq banner endpoint leriniń limiti (promotions.views.PromotionPublicThrottle)
PROMOTION_PUBLIC_THROTTLE_RATE = os.getenv('THROTTLE_PROMOTION_PUBLIC_RATE', '60/min')
# Hár kelwshi mánzili ushın kirisiw hám dizimnen ótiw endpoint leriniń limitleri (users.throttles)
LOGIN_THROTTLE_RATE = os.getenv('THROTTLE_LOGIN_RATE', '10/min')
REGISTER_THROTTLE_RATE = os.getenv('THROTTLE_REGISTER_RATE', '5/min')

# Ashıq juwaptıń (mehmanxana beti, bos orınlar, izlew nátiyjeleri) nusqası keshte saqlanatuǵın sekundlar; 0 onı óshiredi.
# Testler onı óship isleydi, sonda bir test basqasınıń maǵlıwmatın kórmeydi. (common/public_cache.py)
PUBLIC_CACHE_SECONDS = max(int(os.getenv('PUBLIC_CACHE_SECONDS', '0' if TESTING else '30')), 0)

# R16: True bolǵanda (ádetde), rate plan hár qollap-quwatlanatuǵın valyutada iyeniń bahasın alıp júriwi kerek (jaratıw hám
# hár ózgertiw); iye bunı 2026-10-19 de sheshti (qarań .ai/PLAN_R16_MULTI_CURRENCY.md).
RATE_PLAN_PRICES_REQUIRED = os.getenv('RATE_PLAN_PRICES_REQUIRED', 'True').lower() == 'true'

# Celery sazlaması
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
# Worker siz jergilikli development: task lardı (parol tiklew e-mail leri, eskertiwler) soraw ishinde orınlaw
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'False').lower() == 'true'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
# R12: beat kesteleri TIME_ZONE qanday bolsa da is waqtında (Asia/Tashkent) jazıladı.
# Production Celery beat, worker hám Redis tı isletiwi shárt (RELEASE_CHECKLIST).
CELERY_TIMEZONE = BUSINESS_TIME_ZONE

# E-mail (parol tiklew silteme leri). Jergilikli development e-mail di konsolǵa basıp shıǵaradı; production onı
# SMTP arqalı jiberedi hám sayt qayerde ekenin aytıwı kerek, sebebi silteme frontend ke baradı.
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
# Komanda jańa chat xabarı haqqında qayerden biledi (bos = komandaǵa e-mail jiberilmeydi; admin tab ta belgi ele kórinedi)
SUPPORT_NOTIFY_EMAIL = os.getenv('SUPPORT_NOTIFY_EMAIL', '')
PASSWORD_RESET_TIMEOUT = 60 * 60  # tiklew siltemesi bir saat isleydi
# Juwap bermeytuǵın e-mail server web process ti uzaq waqıt ustap turmawı kerek: kod e-mail ı soraw ishinde jiberiledi
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '10'))
# Mánzilge e-mail penen jiberiletuǵın altı sanlı kodlar (users/email_codes.py): dizimnen ótkende akkaunt kod
# terilgennen keyin ǵana jaratıladı, hám mehmann yamasa mehmanxana iyesiniń hár kirisiwine paroldan keyin biri kerek. Ekewine de
# isleytuǵın e-mail kerek (EMAIL_HOST).
EMAIL_VERIFICATION_REQUIRED = os.getenv('EMAIL_VERIFICATION_REQUIRED', 'True').lower() == 'true'
EMAIL_LOGIN_CODE_REQUIRED = os.getenv('EMAIL_LOGIN_CODE_REQUIRED', 'True').lower() == 'true'

# Telegram chatqa eskertiwler (common/alerts.py). Ekewi de bos = eskertiwler óshken. Botti
# @BotFather menen jaratıń, chatqa qosıń hám chat id sin getUpdates shaqırıwınan alıń.
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_ALERT_CHAT_ID = os.getenv('TELEGRAM_ALERT_CHAT_ID', '')

# Dáwirli tapsırmalar (mınadan isletiledi: celery -A config beat -l info)
EXPIRED_BOOKINGS_INTERVAL_SECONDS = int(os.getenv('EXPIRED_BOOKINGS_INTERVAL_SECONDS', '60'))
CELERY_BEAT_SCHEDULE = {
    # Kútip turǵan bronlardıń múddeti 15 minuttan keyin ótedi; olardıń inventory in tez bosatıw
    'expire-pending-bookings': {
        'task': 'bookings.tasks.expire_pending_bookings',
        'schedule': EXPIRED_BOOKINGS_INTERVAL_SECONDS,
    },
    # Mehmanı bergen waqıttan keyin ARRIVAL_GRACE_HOURS saat kelmegen tastıyıqlanǵan bron biykar etiledi
    'cancel-unarrived-bookings': {
        'task': 'bookings.tasks.cancel_unarrived_bookings',
        'schedule': crontab(minute='*/10'),
    },
    # CBU valyuta kursları Asia/Tashkent 09:00 hám 18:00 de (CELERY_TIMEZONE)
    'fetch-exchange-rates': {
        'task': 'currency.tasks.fetch_exchange_rates',
        'schedule': crontab(hour='9,18', minute=0),
    },
    # R12: shıǵıw sanası ótken tastıyıqlanǵan turıwlar completed boladı, Asia/Tashkent 00:05
    'complete-finished-stays': {
        'task': 'bookings.tasks.complete_finished_stays',
        'schedule': crontab(hour=0, minute=5),
    },
    # Aylıq reklama jańalaw: "mehmanxana keyingi ay ushın tólep pe?" dep soraw, waqtında jańalanbaǵan reklamalardı alıp taslaw,
    # Asia/Tashkent 00:05
    # (tómendegi 00:10 tazalawdan aldın, ol ashıq sorawı bar reklamanı isletip qaldıradı)
    'run-ad-renewals': {
        'task': 'promotions.tasks.run_ad_renewals',
        'schedule': crontab(hour=0, minute=5),
    },
    # R10: múddeti ótken mehmanxana reklamaları tamamlanadı, baslanǵan tólengenleri aktiv boladı, Asia/Tashkent 00:10
    'end-expired-promotions': {
        'task': 'promotions.tasks.end_expired_promotions',
        'schedule': crontab(hour=0, minute=10),
    },
    # Múddeti ótken kirisiw session ları database degi basqa hesh nárse alıp taslamaytuǵın qatarlar, Asia/Tashkent 03:30
    'clear-expired-sessions': {
        'task': 'common.tasks.clear_expired_sessions',
        'schedule': crontab(hour=3, minute=30),
    },
}

# Valyuta kursları (R6). Shegaralar environment ten keledi; qarań currency/cbu.py
FX_STALE_AFTER_DAYS = int(os.getenv('FX_STALE_AFTER_DAYS', '3'))
FX_MAX_CHANGE = Decimal(os.getenv('FX_MAX_CHANGE', '0.10'))      # 10 % tan sekirewdi biykar etiw
FX_MIN_RATE = Decimal(os.getenv('FX_MIN_RATE', '1000'))          # UZS / USD, aqılǵa muwapıq aralıq
FX_MAX_RATE = Decimal(os.getenv('FX_MAX_RATE', '100000'))
FX_FETCH_TIMEOUT = int(os.getenv('FX_FETCH_TIMEOUT', '10'))      # sekund

# R12 Status: CSV eksportlar usı qatar sanınan keyin toqtaydı (keyin aqırǵı "truncated" qatarı)
CSV_EXPORT_MAX_ROWS = int(os.getenv('CSV_EXPORT_MAX_ROWS', '10000'))
# R12: mehmanxanalar shıǵıwdan keyin usı kúnge shekem no-show haqqında xabarlay aladı (3-basqısh), sol sebepli
# sol oynanıń Status "stayed" sanları ele ózgeriwi múmkin
NO_SHOW_REPORT_WINDOW_DAYS = int(os.getenv('NO_SHOW_REPORT_WINDOW_DAYS', '7'))
# Naqd bronlar: mehmanxana bron biykar etilgenshe mehmannıń bergen keliw waqtınan keyin kútetuǵın saatlar
ARRIVAL_GRACE_HOURS = int(os.getenv('ARRIVAL_GRACE_HOURS', '2'))
# R12 3-basqısh: mehmanxana staff náwbetinde sońǵı NO_SHOW_FLAG_DAYS kúnde eń keminde
# NO_SHOW_FLAG_MIN_REPORTS esabatı bolsa HÁM esabat dárejesi platforma dárejesiniń eń keminde NO_SHOW_FLAG_FACTOR
# ese bolsa HÁM eń keminde NO_SHOW_FLAG_MIN_RATE bolsa belgilenedi (sol sebepli nolge jaqın ortasha hámmeni belgilemeydi)
NO_SHOW_FLAG_DAYS = int(os.getenv('NO_SHOW_FLAG_DAYS', '90'))
NO_SHOW_FLAG_MIN_REPORTS = int(os.getenv('NO_SHOW_FLAG_MIN_REPORTS', '5'))
NO_SHOW_FLAG_FACTOR = Decimal(os.getenv('NO_SHOW_FLAG_FACTOR', '3'))
NO_SHOW_FLAG_MIN_RATE = Decimal(os.getenv('NO_SHOW_FLAG_MIN_RATE', '0.10'))

# Database ulanıwı jaǵdayın tekseriw

# Production qáwipsiz emes sazlamalar menen iske túspeydi (R4 qáwipsizlik tekseriwi).
# Jergilikli development (DEBUG=True) hám test isleniwi óz ádetdegilerin saqlaydı.
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
    # N-3: belgilenbegen "proxy joq" degen mánis, hám nginx artında hár kelwshi bir IP ni bólisedi, sol sebepli kirisiw
    # throttle i, akkaunt lockout ı hám reklama sanaǵıshları bir sebetke jıynaladı
    if _NUM_PROXIES_ERROR:
        errors.append(_NUM_PROXIES_ERROR)
    elif os.getenv('NUM_PROXIES') is None:
        errors.append('NUM_PROXIES must be set (0 = no reverse proxy, 1 = one nginx/load balancer in front)')
    # N-6: https májbúrlenwi kerek, hám TLS di tamamlaytuǵın proxy header ine isenim kerek
    if not SECURE_SSL_REDIRECT:
        errors.append('SECURE_SSL_REDIRECT must be True when DEBUG is False')
    if NUM_PROXIES > 0 and SECURE_PROXY_SSL_HEADER is None:
        errors.append('USE_X_FORWARDED_PROTO must be True behind a reverse proxy (otherwise the https redirect loops)')
    # Parol tiklew: e-mail ǵa jiberilgen silteme frontend ke baradı hám jiberiw ushın e-mail server kerek
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
    # docker-compose.yml óziniń database konteynerin `db` dep ataydı hám oǵan sol bir mashinadaǵı Docker tiń óz
    # tarmaǵı arqalı jetedi: DB_NETWORK_IS_PRIVATE=True sonı aytadı, hám tek ápiwayı xızmet atı (nuqta joq, IP joq) esapqa
    # alınadı
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
    """localhost, *.localhost / *.local at yamasa IP mánzil: programmistiń óz mashinası bola alatuǵın orınlar."""
    host = host.strip('[]')
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return host == 'localhost' or host.endswith(('.localhost', '.local'))


if DEBUG and not TESTING and not all(_is_local_host(host) for host in ALLOWED_HOSTS):
    # DEBUG stack trace lerdi kórsetedi, API hújjetlerin ashadı hám tómendegi hár tekseriwdi ótkizip jiberedi: ashıq domen de
    # hesh qashan
    raise ValueError('DEBUG must be False when ALLOWED_HOSTS lists a public host name')

if not DEBUG and not TESTING:
    _errors = _production_config_errors()
    if _errors:
        raise ValueError(
            'Insecure production settings (DEBUG is False). On your own computer set DEBUG=True in backend/.env.\n- '
            + '\n- '.join(_errors)
        )
