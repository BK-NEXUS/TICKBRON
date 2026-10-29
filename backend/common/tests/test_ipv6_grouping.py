"""
An IPv6 visitor owns a whole /64 block of addresses and can change address at will, so limits and
lockouts count the block, not the single address. IPv4 stays per address.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from common.request import network_key
from users import lockout
from users.models import User

LOGIN_URL = '/api/v1/auth/login/'


class TestNetworkKey(TestCase):
    def test_ipv4_is_the_address_itself(self):
        assert network_key('203.0.113.7') == '203.0.113.7'

    def test_ipv6_addresses_in_one_64_block_share_a_key(self):
        assert network_key('2001:db8:1:2::1') == network_key('2001:db8:1:2:aaaa:bbbb:cccc:dddd')

    def test_ipv6_addresses_in_different_blocks_differ(self):
        assert network_key('2001:db8:1:2::1') != network_key('2001:db8:1:3::1')

    def test_an_ipv4_address_written_as_ipv6_is_the_ipv4_address(self):
        assert network_key('::ffff:203.0.113.7') == '203.0.113.7'

    def test_nothing_or_garbage_gives_unknown(self):
        assert network_key(None) is None
        assert network_key('not-an-ip') == 'not-an-ip'


class TestLockoutByBlock(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='owner@example.com', password='correct-password-123')

    def login(self, password, ip):
        return self.client.post(
            LOGIN_URL, {'email': 'owner@example.com', 'password': password}, format='json', REMOTE_ADDR=ip)

    def test_changing_the_address_inside_the_block_does_not_reset_the_lock(self):
        for index in range(lockout.IP_FAILURE_LIMIT):
            self.login('wrong-password', f'2001:db8:1:2::{index + 1}')

        assert self.login('correct-password-123', '2001:db8:1:2::ffff').status_code == 401

    def test_another_block_is_not_affected(self):
        for index in range(lockout.IP_FAILURE_LIMIT):
            self.login('wrong-password', f'2001:db8:1:2::{index + 1}')

        assert self.login('correct-password-123', '2001:db8:9:9::1').status_code == 200


class TestVisitorsAndThrottles(TestCase):
    def test_an_ad_visitor_changing_ipv6_address_inside_the_block_counts_once(self):
        from django.test import RequestFactory

        from promotions.stats import _visitor_hash

        first = RequestFactory().get('/', REMOTE_ADDR='2001:db8:1:2::1')
        second = RequestFactory().get('/', REMOTE_ADDR='2001:db8:1:2:dead:beef:0:7')
        other_block = RequestFactory().get('/', REMOTE_ADDR='2001:db8:1:3::1')

        assert _visitor_hash(first) == _visitor_hash(second)
        assert _visitor_hash(first) != _visitor_hash(other_block)

    def test_the_anonymous_throttle_counts_the_block(self):
        from django.test import RequestFactory
        from rest_framework.request import Request

        from common.throttling import BlockAnonRateThrottle

        def ident(address):
            return BlockAnonRateThrottle().get_ident(Request(RequestFactory().get('/', REMOTE_ADDR=address)))

        assert ident('2001:db8:1:2::1') == ident('2001:db8:1:2::99')
        assert ident('203.0.113.7') == '203.0.113.7'
