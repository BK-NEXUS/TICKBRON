"""
Custom decorators for TICKBRON Backend.

Provides rate limiting, caching, and other utility decorators.
"""
from django.core.cache import cache
from common.request import get_client_ip as _get_client_ip
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from functools import wraps
import logging

logger = logging.getLogger('tickbron')


def rate_limit(limit='100/h', key_func=None):
    """
    Rate limiting decorator for API endpoints.
    
    Args:
        limit: Rate limit string (e.g., '100/h', '1000/d', '10/m')
        key_func: Function to generate cache key (defaults to user ID or IP)
    
    Usage:
        @rate_limit('100/h')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(request)
            elif request.user.is_authenticated:
                cache_key = f"rate_limit:{request.user.id}"
            else:
                cache_key = f"rate_limit:{get_client_ip(request)}"
            
            # Parse limit (e.g., '100/h' -> 100 requests per hour)
            try:
                count, period = limit.split('/')
                count = int(count)
                period_seconds = {
                    's': 1,
                    'm': 60,
                    'h': 3600,
                    'd': 86400
                }.get(period.lower(), 3600)
            except (ValueError, AttributeError):
                logger.error(f"Invalid rate limit format: {limit}")
                count = 100
                period_seconds = 3600
            
            # Check rate limit
            current_count = cache.get(cache_key, 0)
            
            if current_count >= count:
                logger.warning(f"Rate limit exceeded for {cache_key}")
                raise PermissionDenied("Rate limit exceeded. Please try again later.")
            
            # Increment counter
            cache.set(cache_key, current_count + 1, period_seconds)
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    
    return decorator


def get_client_ip(request):
    """Get the client IP address from the request."""
    return _get_client_ip(request)


def class_rate_limit(limit='100/h', key_func=None):
    """
    Rate limiting decorator for class-based views.
    
    Usage:
        @class_rate_limit('100/h')
        class MyView(View):
            ...
    """
    return method_decorator(rate_limit(limit, key_func), name='dispatch')
