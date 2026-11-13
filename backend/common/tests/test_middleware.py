"""
Óz middleware ushın testler.
"""
from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from common.middleware import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    PerformanceMonitoringMiddleware
)


class SecurityHeadersMiddlewareTest(TestCase):
    """SecurityHeadersMiddleware ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.factory = RequestFactory()
        self.middleware = SecurityHeadersMiddleware(lambda request: HttpResponse())

    def test_security_headers_added(self):
        """Qáwipsizlik header leri juwaplarǵa qosılatuǵının testlew."""
        request = self.factory.get('/')
        response = self.middleware(request)

        self.assertIn('X-Content-Type-Options', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertIn('X-Frame-Options', response)
        self.assertIn('X-XSS-Protection', response)
        self.assertIn('Referrer-Policy', response)
        self.assertIn('Permissions-Policy', response)

    def test_permissions_policy_restricts_access(self):
        """Permissions-Policy jasırın API lardı sheklewin testlew."""
        request = self.factory.get('/')
        response = self.middleware(request)

        self.assertIn('Permissions-Policy', response)
        self.assertIn('geolocation=()', response['Permissions-Policy'])
        self.assertIn('microphone=()', response['Permissions-Policy'])
        self.assertIn('camera=()', response['Permissions-Policy'])


class RequestLoggingMiddlewareTest(TestCase):
    """RequestLoggingMiddleware ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.factory = RequestFactory()
        self.middleware = RequestLoggingMiddleware(lambda request: HttpResponse())

    def test_response_time_header_added(self):
        """Juwap waqtı header i qosılatuǵının testlew."""
        request = self.factory.get('/')
        response = self.middleware(request)

        self.assertIn('X-Response-Time', response)
        self.assertTrue(response['X-Response-Time'].endswith('s'))

    def test_authenticated_request_log_does_not_contain_user_email(self):
        """audit #24: hár soraw paydalanıwshını log qa jazadı -- ol onıń e-mail ı (PII) bolmawı kerek."""
        from users.models import User

        user = User.objects.create_user(
            email='pii-should-not-be-logged@example.com',
            password='testpass123'
        )
        request = self.factory.get('/')
        request.user = user

        with self.assertLogs('tickbron', level='INFO') as captured:
            self.middleware(request)

        log_output = '\n'.join(captured.output)
        self.assertNotIn('pii-should-not-be-logged@example.com', log_output)
        self.assertIn(str(user.id), log_output)


class PerformanceMonitoringMiddlewareTest(TestCase):
    """PerformanceMonitoringMiddleware ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.factory = RequestFactory()
        self.middleware = PerformanceMonitoringMiddleware(lambda request: HttpResponse())

    def test_middleware_does_not_break_normal_requests(self):
        """Middleware ápiwayı sorawlardı buzbaytuǵının testlew."""
        request = self.factory.get('/')
        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)


class HstsHeaderTest(TestCase):
    """N-6: HSTS tek HTTPS juwaplarına tiyisli; ol redirect sazlamasına baylanıslı bolmawı kerek."""

    def test_no_hsts_on_a_plain_http_request(self):
        with self.settings(SECURE_SSL_REDIRECT=True, SECURE_HSTS_SECONDS=3600):
            response = self.client.get('/api/v1/auth/csrf/')

        self.assertNotIn('Strict-Transport-Security', response)

    def test_hsts_on_a_secure_request_even_when_redirect_is_off(self):
        with self.settings(SECURE_SSL_REDIRECT=False, SECURE_HSTS_SECONDS=3600,
                           SECURE_HSTS_INCLUDE_SUBDOMAINS=True, SECURE_HSTS_PRELOAD=False):
            response = self.client.get('/api/v1/auth/csrf/', secure=True)

        self.assertEqual(response['Strict-Transport-Security'], 'max-age=3600; includeSubDomains')

    def test_preload_is_added_only_when_enabled(self):
        with self.settings(SECURE_HSTS_SECONDS=3600, SECURE_HSTS_INCLUDE_SUBDOMAINS=False, SECURE_HSTS_PRELOAD=True):
            response = self.client.get('/api/v1/auth/csrf/', secure=True)

        self.assertEqual(response['Strict-Transport-Security'], 'max-age=3600; preload')

    def test_no_hsts_when_the_lifetime_is_zero(self):
        with self.settings(SECURE_HSTS_SECONDS=0):
            response = self.client.get('/api/v1/auth/csrf/', secure=True)

        self.assertNotIn('Strict-Transport-Security', response)
