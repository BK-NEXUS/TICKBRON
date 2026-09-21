"""
Custom exception handlers for TICKBRON Backend.

Provides consistent error responses and logging for API exceptions.
"""
import logging
from django.conf import settings
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from .exceptions import TickBronException

logger = logging.getLogger('tickbron')


def custom_exception_handler(exc, context):
    """
    Custom exception handler for TICKBRON API.
    
    Provides consistent error responses with proper logging.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If response is None, it's a non-API exception
    if response is None:
        # Log unexpected exceptions
        logger.error(
            f"Unexpected exception: {exc.__class__.__name__} - {str(exc)}",
            exc_info=True,
            extra={'context': context}
        )
        
        # Return standardized error response
        return Response(
            {
                'error': {
                    'code': 'internal_error',
                    'message': 'An unexpected error occurred. Please try again later.',
                    'details': str(exc) if settings.DEBUG else None
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Handle TICKBRON custom exceptions
    if isinstance(exc, TickBronException):
        # Log the exception (already logged in exception class)
        logger.info(
            f"TICKBRON exception: {exc.__class__.__name__} - {str(exc)}",
            extra={'context': context}
        )
        
        # Add retry-after header for rate limit exceptions
        headers = {}
        if hasattr(exc, 'retry_after') and exc.retry_after:
            headers['Retry-After'] = str(exc.retry_after)
        
        # Return standardized error response
        return Response(
            {
                'error': {
                    'code': exc.default_code,
                    'message': str(exc.default_detail),
                    'details': str(exc) if exc.detail != exc.default_detail else None
                }
            },
            status=exc.status_code,
            headers=headers
        )
    
    # Log validation errors
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        logger.warning(
            f"Validation error: {str(exc)}",
            extra={'context': context}
        )
    
    # Log permission errors
    if response.status_code == status.HTTP_403_FORBIDDEN:
        logger.warning(
            f"Permission denied: {str(exc)}",
            extra={'context': context}
        )
    
    # Log not found errors
    if response.status_code == status.HTTP_404_NOT_FOUND:
        logger.info(
            f"Resource not found: {str(exc)}",
            extra={'context': context}
        )
    
    # Log rate limit errors
    if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        logger.warning(
            f"Rate limit exceeded: {str(exc)}",
            extra={'context': context}
        )
    
    # Log server errors
    if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(
            f"Server error: {exc.__class__.__name__} - {str(exc)}",
            exc_info=True,
            extra={'context': context}
        )
    
    # Standardize error response format
    if hasattr(response, 'data'):
        # Wrap existing data in error format if not already wrapped
        if not isinstance(response.data, dict) or 'error' not in response.data:
            response.data = {
                'error': {
                    'code': response.data.get('code', 'error'),
                    'message': response.data.get('detail', str(response.data)),
                    'details': response.data
                }
            }
    
    return response
