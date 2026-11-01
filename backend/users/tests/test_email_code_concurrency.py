"""A mailed code is single use even when two requests present it at the same moment."""
import threading
import uuid
from unittest import SkipTest

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.test import SimpleTestCase, override_settings

from users import email_codes

REDIS_CACHES = {'default': {'BACKEND': 'django_redis.cache.RedisCache', 'LOCATION': settings.REDIS_URL,
                            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                                        'SOCKET_CONNECT_TIMEOUT': 1, 'SOCKET_TIMEOUT': 1}}}


@override_settings(CACHES=REDIS_CACHES)
class VerifyOnceTests(SimpleTestCase):
    """Run on Redis, the production cache: the in-process test cache serializes the race away."""

    def setUp(self):
        try:
            cache.set('race-test-ping', 1, 5)
        except Exception as error:
            raise SkipTest(f'Redis is not reachable: {error}')

    def test_parallel_verifications_of_one_code_succeed_once(self):
        for round_number in range(40):
            ident = f'race-{uuid.uuid4().hex}'
            email_codes.issue('signup', ident, 'race@example.com', payload={'k': 'v'})
            code = self._live_code()
            outcomes = self._verify_together(ident, code, threads=4)
            assert sum(1 for outcome in outcomes if outcome is not None) == 1, f'round {round_number}'

    @staticmethod
    def _verify_together(ident, code, threads):
        barrier = threading.Barrier(threads)
        outcomes = []

        def attempt():
            barrier.wait(timeout=10)
            outcomes.append(email_codes.verify('signup', ident, code))
            connection.close()

        workers = [threading.Thread(target=attempt) for _ in range(threads)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=30)
        return outcomes

    @staticmethod
    def _live_code():
        from django.core import mail
        body = mail.outbox[-1].body
        return next(word for word in body.split() if email_codes.looks_like_a_code(word))
