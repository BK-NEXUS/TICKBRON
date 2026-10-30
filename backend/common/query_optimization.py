"""
Query optimization utilities for TICKBRON Backend.

Provides helper functions for database query optimization and monitoring.
"""
import logging
from django.db import connection, reset_queries
from django.conf import settings

logger = logging.getLogger('tickbron')


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
