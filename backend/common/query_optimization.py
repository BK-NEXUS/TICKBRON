"""
Query optimization utilities for TICKBRON Backend.

Provides helper functions for database query optimization and monitoring.
"""
import logging
from django.db import connection, reset_queries
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('tickbron')


class QueryOptimizationMixin:
    """
    Mixin for viewsets to provide query optimization features.
    """
    
    def get_queryset(self):
        """
        Get optimized queryset with select_related and prefetch_related.
        
        Override this method in viewsets to add custom optimization.
        """
        queryset = super().get_queryset()
        
        # Only optimize in non-debug mode
        if not settings.DEBUG:
            queryset = self.optimize_queryset(queryset)
        
        return queryset
    
    def optimize_queryset(self, queryset):
        """
        Apply query optimization strategies to the queryset.
        
        Override this method to implement custom optimization logic.
        """
        # Log query count for monitoring
        if settings.DEBUG:
            reset_queries()
        
        return queryset


def log_query_count(func):
    """
    Decorator to log database query count for views.
    
    Usage:
        @log_query_count
        def my_view(request):
            ...
    """
    def wrapper(*args, **kwargs):
        if settings.DEBUG:
            reset_queries()
            result = func(*args, **kwargs)
            query_count = len(connection.queries)
            logger.info(f"Query count for {func.__name__}: {query_count}")
            
            # Log slow queries (> 100ms)
            for query in connection.queries:
                time = float(query['time'])
                if time > 0.1:  # 100ms
                    logger.warning(f"Slow query ({time:.3f}s): {query['sql'][:200]}")
            
            return result
        else:
            return func(*args, **kwargs)
    
    return wrapper


def cache_query_result(cache_key, timeout=300):
    """
    Decorator to cache query results.
    
    Args:
        cache_key: Cache key (can be a format string)
        timeout: Cache timeout in seconds (default: 5 minutes)
    
    Usage:
        @cache_query_result('property_{property_id}', timeout=3600)
        def get_property_detail(property_id):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from arguments
            if '{' in cache_key:
                key = cache_key.format(**kwargs)
            else:
                key = cache_key
            
            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit for {key}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, timeout)
            logger.debug(f"Cache miss for {key}, cached for {timeout}s")
            
            return result
        return wrapper
    return decorator


class QueryPerformanceMonitor:
    """
    Context manager to monitor query performance.
    
    Usage:
        with QueryPerformanceMonitor('my_operation'):
            # Perform database operations
            ...
    """
    
    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.query_count_before = 0
        self.query_count_after = 0
    
    def __enter__(self):
        if settings.DEBUG:
            reset_queries()
            self.query_count_before = len(connection.queries)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if settings.DEBUG:
            self.query_count_after = len(connection.queries)
            query_count = self.query_count_after - self.query_count_before
            
            total_time = sum(float(q['time']) for q in connection.queries[self.query_count_before:])
            
            logger.info(
                f"Query performance for {self.operation_name}: "
                f"{query_count} queries, {total_time:.3f}s total"
            )
            
            if query_count > 50:
                logger.warning(f"High query count detected for {self.operation_name}: {query_count}")
            
            if total_time > 1.0:
                logger.warning(f"Slow query time detected for {self.operation_name}: {total_time:.3f}s")
        
        return False
