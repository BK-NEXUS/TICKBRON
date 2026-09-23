"""
Tests for client IP detection behind proxies (audit #10).
"""
from unittest import mock

from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIClient

from common.request import get_client_ip
from users.models import User


class TestGetClientIp(TestCase):
    def request(self, remote_addr='10.0.0.1', forwarded_for=None):
        meta = {'REMOTE_ADDR': remote_addr}
        if forwarded_for is not None:
            meta['HTTP_X_FORWARDED_FOR'] = forwarded_for
        return RequestFactory().get('/', **meta)

    @override_settings(NUM_PROXIES=0)
    def test_header_is_ignored_without_trusted_proxies(self):
        assert get_client_ip(self.request(forwarded_for='6.6.6.6')) == '10.0.0.1'

    @override_settings(NUM_PROXIES=1)
    def test_one_proxy_uses_the_address_it_appended(self):
        # Client forged "6.6.6.6"; the proxy appended the real peer 203.0.113.7
        request = self.request(forwarded_for='6.6.6.6, 203.0.113.7')
        assert get_client_ip(request) == '203.0.113.7'

    @override_settings(NUM_PROXIES=2)
    def test_two_proxies(self):
        request = self.request(forwarded_for='6.6.6.6, 203.0.113.7, 10.1.1.1')
        assert get_client_ip(request) == '203.0.113.7'

    @override_settings(NUM_PROXIES=1)
    def test_missing_header_falls_back_to_remote_addr(self):
        assert get_client_ip(self.request()) == '10.0.0.1'

    @override_settings(NUM_PROXIES=1)
    def test_invalid_address_falls_back_to_remote_addr(self):
        assert get_client_ip(self.request(forwarded_for='not-an-ip')) == '10.0.0.1'


@mock.patch('users.views.TESTING', False)
class TestForgedForwardedForDoesNotBypassThrottling(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.client = APIClient()

    def test_login_throttle_counts_by_real_ip(self):
        responses = [
            self.client.post('/api/v1/auth/login/', {'email': 'nobody@example.com', 'password': 'x'},
                             format='json', REMOTE_ADDR='10.0.0.9', HTTP_X_FORWARDED_FOR=f'6.6.6.{i}')
            for i in range(11)
        ]

        assert all(r.status_code != 429 for r in responses[:10])
        assert responses[10].status_code == 429

    def test_stored_login_ip_is_not_forgeable(self):
        user = User.objects.create_user(email='ip@example.com', password='correct-password-123')

        response = self.client.post(
            '/api/v1/auth/login/', {'email': 'ip@example.com', 'password': 'correct-password-123'},
            format='json', REMOTE_ADDR='10.0.0.9', HTTP_X_FORWARDED_FOR='6.6.6.6'
        )

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.last_login_ip == '10.0.0.9'
