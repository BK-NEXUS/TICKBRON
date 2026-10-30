"""
Custom middleware for TICKBRON Backend.

Provides security headers, request logging, and performance monitoring.
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
    """A caller-chosen value made safe for one log line: a newline in it would start a forged line."""
    return _CONTROL_CHARACTERS.sub(lambda match: match.group().encode('unicode_escape').decode(), str(value))


MAX_JSON_BODY_BYTES = 4 * 1024 * 1024  # real API bodies are under 100 KB; nginx stops at 1 MB first
MAX_UPLOAD_BODY_BYTES = 12 * 1024 * 1024  # photo upload: 10 MB image plus form overhead


class RequestLanguageMiddleware(LocaleMiddleware):
    """The language of the request (Accept-Language: uz, ru or en) for its own duration only."""

    def process_response(self, request, response):
        response = super().process_response(request, response)
        # The thread is reused: code outside a request (tasks, tests) must not inherit this language
        translation.deactivate()
        return response


class RequestBodyLimitMiddleware:
    """
    Refuse an oversized body from its Content-Length header, before any view reads it.

    DRF's JSON parser reads the stream directly, so Django's DATA_UPLOAD_MAX_MEMORY_SIZE does not
    stop one huge JSON request from being buffered by a worker. nginx should enforce the same limits.
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
    Answer 400 to a query string that carries a NUL character (%00).

    PostgreSQL can neither store nor search for it, so a search box would otherwise answer 500. A NUL inside a JSON
    body is left to the field checks (which name the field) and, for text nobody checks, to the exception handler.
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
    Middleware to add security headers to all responses.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = getattr(settings, 'X_FRAME_OPTIONS', 'DENY')
        response['X-XSS-Protection'] = '0'  # the legacy auditor can be abused to leak data; CSP is the defence
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Strict-Transport-Security comes from Django's SecurityMiddleware (SECURE_HSTS_* settings):
        # it sends it on HTTPS requests only, which a second copy here got wrong behind a proxy
        
        return response


class RequestLoggingMiddleware:
    """
    Middleware to log HTTP requests for monitoring and debugging.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Log request. Use the user's id, not str(user) (the user's email), so
        # PII does not end up in every request log line.
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
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} - "
            f"Duration: {duration:.3f}s - "
            f"Path: {printable(request.path)}"
        )
        
        # Add response time header for monitoring
        response['X-Response-Time'] = f'{duration:.3f}s'
        
        return response
    
    def get_client_ip(self, request):
        """
        Get the client IP address from the request.
        
        Handles proxied requests (X-Forwarded-For header).
        """
        return get_client_ip(request)


class PerformanceMonitoringMiddleware:
    """
    Middleware to monitor slow requests and database queries.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_request_threshold = 2.0  # 2 seconds default
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log slow requests
        if duration > self.slow_request_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {printable(request.path)} - "
                f"Duration: {duration:.3f}s - "
                f"IP: {self.get_client_ip(request)}"
            )
        
        return response
    
    def get_client_ip(self, request):
        """Get the client IP address from the request."""
        return get_client_ip(request)
