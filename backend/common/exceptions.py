"""
Custom exceptions for TICKBRON Backend.

Provides structured error handling with proper logging.
"""
import logging
from rest_framework.exceptions import APIException
from rest_framework import status

logger = logging.getLogger('tickbron')


class TickBronException(APIException):
    """
    Base exception for TICKBRON-specific errors.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'A server error occurred.'
    default_code = 'server_error'
    
    def __init__(self, detail=None, code=None, log_level='error'):
        self.log_level = log_level
        super().__init__(detail, code)
        
        # Log the exception
        log_method = getattr(logger, log_level, logger.error)
        log_method(f"{self.__class__.__name__}: {self.detail}")


class RateLimitException(TickBronException):
    """
    Exception raised when rate limit is exceeded.
    """
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Rate limit exceeded. Please try again later.'
    default_code = 'rate_limit_exceeded'
    
    def __init__(self, detail=None, retry_after=None):
        if detail is None:
            detail = self.default_detail
        super().__init__(detail, log_level='warning')
        self.retry_after = retry_after


class PermissionDeniedException(TickBronException):
    """
    Exception raised when user lacks required permissions.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'permission_denied'
    
    def __init__(self, detail=None):
        if detail is None:
            detail = self.default_detail
        super().__init__(detail, log_level='warning')


class ResourceNotFoundException(TickBronException):
    """
    Exception raised when a requested resource is not found.
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found.'
    default_code = 'not_found'
    
    def __init__(self, detail=None):
        if detail is None:
            detail = self.default_detail
        super().__init__(detail, log_level='info')


class ValidationException(TickBronException):
    """
    Exception raised when validation fails.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid input data.'
    default_code = 'validation_error'
    
    def __init__(self, detail=None):
        if detail is None:
            detail = self.default_detail
        super().__init__(detail, log_level='warning')


class ExternalServiceException(TickBronException):
    """
    Exception raised when an external service call fails.
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'External service unavailable.'
    default_code = 'external_service_error'
    
    def __init__(self, detail=None, service_name=None):
        if detail is None:
            detail = self.default_detail
        if service_name:
            detail = f"{service_name}: {detail}"
        super().__init__(detail, log_level='error')
