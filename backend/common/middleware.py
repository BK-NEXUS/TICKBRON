"""
Custom middleware for TICKBRON Backend.

Provides security headers, request logging, and performance monitoring.
"""
import time
import logging
from django.conf import settings

logger = logging.getLogger('tickbron')


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
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # HSTS headers (only in production with HTTPS)
        if getattr(settings, 'SECURE_SSL_REDIRECT', False):
            hsts_seconds = getattr(settings, 'SECURE_HSTS_SECONDS', 31536000)
            hsts_include_subdomains = getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', True)
            hsts_preload = getattr(settings, 'SECURE_HSTS_PRELOAD', True)
            
            hsts_value = f'max-age={hsts_seconds}'
            if hsts_include_subdomains:
                hsts_value += '; includeSubDomains'
            if hsts_preload:
                hsts_value += '; preload'
            
            response['Strict-Transport-Security'] = hsts_value
        
        return response


class RequestLoggingMiddleware:
    """
    Middleware to log HTTP requests for monitoring and debugging.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Log request
        user_info = 'Anonymous'
        if hasattr(request, 'user'):
            user_info = str(request.user) if request.user.is_authenticated else 'Anonymous'
        
        logger.info(
            f"Request: {request.method} {request.path} - "
            f"IP: {self.get_client_ip(request)} - "
            f"User: {user_info}"
        )
        
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} - "
            f"Duration: {duration:.3f}s - "
            f"Path: {request.path}"
        )
        
        # Add response time header for monitoring
        response['X-Response-Time'] = f'{duration:.3f}s'
        
        return response
    
    def get_client_ip(self, request):
        """
        Get the client IP address from the request.
        
        Handles proxied requests (X-Forwarded-For header).
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


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
                f"Slow request detected: {request.method} {request.path} - "
                f"Duration: {duration:.3f}s - "
                f"IP: {self.get_client_ip(request)}"
            )
        
        return response
    
    def get_client_ip(self, request):
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
