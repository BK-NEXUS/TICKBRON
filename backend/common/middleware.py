"""
Custom middleware for TICKBRON Backend.

Provides security headers, request logging, and performance monitoring.
"""
import time
import logging
from django.conf import settings
from common.request import get_client_ip

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
                f"Slow request detected: {request.method} {request.path} - "
                f"Duration: {duration:.3f}s - "
                f"IP: {self.get_client_ip(request)}"
            )
        
        return response
    
    def get_client_ip(self, request):
        """Get the client IP address from the request."""
        return get_client_ip(request)
