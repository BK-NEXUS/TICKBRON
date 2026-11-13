"""
TICKBRON Backend ushın óz middleware i.

Qáwipsizlik header leri, sorawlardı log lawdı hám ónimdarlıq monitoring in támiyinleydi.
"""
import re
from urllib.parse import unquote
import time
import logging
from django.conf import settings
from django.http import JsonResponse
from django.middleware.locale import LocaleMiddleware
from django.utils import translation
from common.request import get_client_ip, reset_current_ip, set_current_ip

logger = logging.getLogger('tickbron')

_CONTROL_CHARACTERS = re.compile(r'[\x00-\x1f\x7f-\x9f\u2028\u2029]')


def printable(value):
    """Bir log qatarı ushın qáwipsiz etilgen shaqırıwshı tańlaǵan mánis: ondaǵı jańa qatar jalǵan qatar baslar edi."""
    return _CONTROL_CHARACTERS.sub(lambda match: match.group().encode('unicode_escape').decode(), str(value))


MAX_JSON_BODY_BYTES = 4 * 1024 * 1024  # haqıyqıy API denelerı 100 KB tan kem; nginx aldın 1 MB da toqtaydı
MAX_UPLOAD_BODY_BYTES = 12 * 1024 * 1024  # súwret júklew: 10 MB súwret hám forma qosımsha ólshemi


class RequestLanguageMiddleware(LocaleMiddleware):
    """Sorawdıń tili (Accept-Language: uz, ru yamasa en) tek óz dawamlılıǵı ushın."""

    def process_response(self, request, response):
        response = super().process_response(request, response)
        # Thread qayta paydalanıladı: soraw sırtındaǵı kod (task lar, testler) bul tildi miyras almawı kerek
        translation.deactivate()
        return response


class RequestBodyLimitMiddleware:
    """
    Artıq úlken denení Content-Length header inen, qálegen view oqıp úlgermesten biykar etiw.

    DRF tiń JSON parser i aǵımdı tikkeley oqıydı, sol sebepli Django nıń DATA_UPLOAD_MAX_MEMORY_SIZE
    bir úlken JSON sorawdıń worker ge buffer ge alınıwın toqtatpaydı. nginx sol shekleulerdi de májbúrlewi kerek.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            length = int(request.META.get('CONTENT_LENGTH') or 0)
        except ValueError:
            length = 0
        upload = request.content_type.startswith('multipart/')
        if length > (MAX_UPLOAD_BODY_BYTES if upload else MAX_JSON_BODY_BYTES):
            return JsonResponse(
                {'error': {'code': 'payload_too_large', 'message': 'The request body is too large.', 'details': None}},
                status=413,
            )
        return self.get_response(request)


class RejectNullCharactersMiddleware:
    """
    NUL belgisi (%00) bar query string ke 400 menen juwap beriw.

    PostgreSQL onı saqlay da, izley de almaydı, sol sebepli izlew qutısı basqasha 500 beredi. JSON denesindegi NUL
    maydan tekseriwine (maydandı ataydı) hám hesh kim tekspeytuǵın tekst ushın exception handler ge qaldırıladı.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if '\x00' in unquote(request.META.get('QUERY_STRING', '')):
            return JsonResponse(
                {'error': {'code': 'invalid_input', 'message': 'The request contains a character that is not allowed.',
                           'details': None}},
                status=400,
            )
        return self.get_response(request)


class SecurityHeadersMiddleware:
    """
    Barlıq juwaplarǵa qáwipsizlik header lerin qosatuǵın middleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Qáwipsizlik header lerin qosıw
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = getattr(settings, 'X_FRAME_OPTIONS', 'DENY')
        response['X-XSS-Protection'] = '0'  # eski auditor maǵlıwmattı sızdırıw ushın paydalanılıwı múmkin; CSP bul qorǵanıs
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        # Strict-Transport-Security Django nıń SecurityMiddleware inen keledi (SECURE_HSTS_* sazlamaları):
        # ol tek HTTPS sorawlarında jiberiledi, bul jerdegi ekinshi nusqa proxy artında qátelesti

        return response


class RequestLoggingMiddleware:
    """
    Monitoring hám debug ushın HTTP sorawların log laytuǵın middleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        # Sorawdı log qa jazıw. str(user) (paydalanıwshınıń e-mail ı) emes, paydalanıwshınıń id sin paydalanıń, sonda
        # PII hár soraw log qatarına túspeydi.
        user_info = 'Anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info = f'user:{request.user.id}'

        logger.info(
            f"Request: {request.method} {printable(request.path)} - "
            f"IP: {self.get_client_ip(request)} - "
            f"User: {user_info}"
        )

        token = set_current_ip(self.get_client_ip(request))
        try:
            response = self.get_response(request)
        finally:
            reset_current_ip(token)

        # Dawamlılıqtı esaplaw
        duration = time.time() - start_time

        # Juwaptı log qa jazıw
        logger.info(
            f"Response: {response.status_code} - "
            f"Duration: {duration:.3f}s - "
            f"Path: {printable(request.path)}"
        )

        # Monitoring ushın juwap waqtı header in qosıw
        response['X-Response-Time'] = f'{duration:.3f}s'

        return response

    def get_client_ip(self, request):
        """
        Sorawdan klient IP mánzilin alıw.

        Proxy arqalı kelgen sorawlardı islewdi biledi (X-Forwarded-For header).
        """
        return get_client_ip(request)


class PerformanceMonitoringMiddleware:
    """
    Sekin sorawlardı hám database query lerin baqlaytuǵın middleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_request_threshold = 2.0  # ádetde 2 sekund

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        # Sekin sorawlardı log qa jazıw
        if duration > self.slow_request_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {printable(request.path)} - "
                f"Duration: {duration:.3f}s - "
                f"IP: {self.get_client_ip(request)}"
            )

        return response

    def get_client_ip(self, request):
        """Sorawdan klient IP mánzilin alıw."""
        return get_client_ip(request)
