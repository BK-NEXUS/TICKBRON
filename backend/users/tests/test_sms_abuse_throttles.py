"""
A06-1 / A06-2: nobody can make the system send an unlimited number of SMS.

The limits that already existed were keyed on a phone number taken from the request body, so
a new number in every request was a new, empty bucket, and the logged-in verification
endpoints (which ignore the body) were bypassed the same way.
"""
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from users import views
from users.models import User

PATCH_TESTING = patch('users.views.TESTING', False)


class _Base(TestCase):
    def setUp(self):
        cache.clear()
        PATCH_TESTING.start()
        self.addCleanup(PATCH_TESTING.stop)
        self.addCleanup(cache.clear)


class PhoneVerificationRequestThrottleTests(_Base):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(email='a@example.com', password='x', phone_number='+998901112233')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _request(self, body=None):
        return self.client.post('/api/v1/auth/phone/verify/request/', body or {}, format='json')

    def test_a_different_phone_number_in_each_body_does_not_reset_the_limit(self):
        codes = [self._request({'phone_number': f'+99890000{n:04d}'}).status_code for n in range(5)]

        assert codes[:3] == [200, 200, 200]
        assert codes[3:] == [429, 429]

    def test_the_limit_is_per_account_not_shared(self):
        for _ in range(3):
            self._request()
        other = User.objects.create_user(email='b@example.com', password='x', phone_number='+998905556677')
        client = APIClient()
        client.force_authenticate(other)

        assert client.post('/api/v1/auth/phone/verify/request/', {}, format='json').status_code == 200

    def test_the_confirm_endpoint_has_the_same_protection(self):
        codes = [
            self.client.post('/api/v1/auth/phone/verify/confirm/', {'otp_code': '000000', 'phone_number': f'+99890000{n:04d}'},
                             format='json').status_code
            for n in range(7)
        ]

        assert codes[:5] == [400] * 5
        assert codes[5:] == [429, 429]

    def test_one_number_gets_a_daily_budget_of_codes(self):
        with patch.object(views.OTPDailyNumberThrottle, 'rate', '2/day'):
            codes = [self._request().status_code for _ in range(3)]

        assert codes == [200, 200, 429]

    def test_one_account_gets_a_daily_budget_of_verification_requests(self):
        with patch.object(views.PhoneVerifyDailyThrottle, 'rate', '2/day'):
            codes = [self._request().status_code for _ in range(3)]

        assert codes == [200, 200, 429]


class LoginOtpRequestBudgetTests(_Base):
    def _request(self, phone):
        return APIClient().post('/api/v1/auth/otp/request/', {'phone_number': phone}, format='json')

    def test_a_new_number_each_time_is_stopped_by_the_ip_budget(self):
        with patch.object(views.OTPRequestIPThrottle, 'rate', '3/hour'):
            codes = [self._request(f'+99890111{n:04d}').status_code for n in range(5)]

        assert codes == [200, 200, 200, 429, 429]

    def test_one_number_gets_a_daily_budget_of_codes(self):
        with patch.object(views.OTPDailyNumberThrottle, 'rate', '2/day'):
            codes = [self._request('+998901112233').status_code for _ in range(3)]

        assert codes == [200, 200, 429]


class SharedBudgetTests(_Base):
    def test_a_logged_in_caller_cannot_use_their_own_number_to_dodge_the_budget_of_another(self):
        user = User.objects.create_user(email='a@example.com', password='x', phone_number='+998901112233')
        client = APIClient()
        client.force_authenticate(user)
        victim = '+998907778899'

        with patch.object(views.OTPDailyNumberThrottle, 'rate', '2/day'):
            codes = [client.post('/api/v1/auth/otp/request/', {'phone_number': victim}, format='json').status_code
                     for _ in range(3)]

        assert codes == [200, 200, 429]
