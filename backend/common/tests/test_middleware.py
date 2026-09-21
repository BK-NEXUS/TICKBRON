"""
Tests for custom middleware.
"""
import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from common.middleware import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    PerformanceMonitoringMiddleware
)


class SecurityHeadersMiddlewareTest(TestCase):
    """Tests for SecurityHeadersMiddleware."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.middleware = SecurityHeadersMiddleware(lambda request: HttpResponse())
    
    def test_security_headers_added(self):
        """Test that security headers are added to responses."""
        request = self.factory.get('/')
        response = self.middleware(request)
        
        self.assertIn('X-Content-Type-Options', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertIn('X-Frame-Options', response)
        self.assertIn('X-XSS-Protection', response)
        self.assertIn('Referrer-Policy', response)
        self.assertIn('Permissions-Policy', response)
    
    def test_permissions_policy_restricts_access(self):
        """Test that Permissions-Policy restricts sensitive APIs."""
        request = self.factory.get('/')
        response = self.middleware(request)
        
        self.assertIn('Permissions-Policy', response)
        self.assertIn('geolocation=()', response['Permissions-Policy'])
        self.assertIn('microphone=()', response['Permissions-Policy'])
        self.assertIn('camera=()', response['Permissions-Policy'])


class RequestLoggingMiddlewareTest(TestCase):
    """Tests for RequestLoggingMiddleware."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.middleware = RequestLoggingMiddleware(lambda request: HttpResponse())
    
    def test_response_time_header_added(self):
        """Test that response time header is added."""
        request = self.factory.get('/')
        response = self.middleware(request)
        
        self.assertIn('X-Response-Time', response)
        self.assertTrue(response['X-Response-Time'].endswith('s'))


class PerformanceMonitoringMiddlewareTest(TestCase):
    """Tests for PerformanceMonitoringMiddleware."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.middleware = PerformanceMonitoringMiddleware(lambda request: HttpResponse())
    
    def test_middleware_does_not_break_normal_requests(self):
        """Test that middleware doesn't break normal requests."""
        request = self.factory.get('/')
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
