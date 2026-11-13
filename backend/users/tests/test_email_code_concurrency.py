"""Pochta menen jiberilgen kod eki sorawdıń birdey waqıtta usınıwında da bir ret qollanıladı."""
import re
import threading
import uuid
from unittest import mock

from django.core import mail
from django.test import SimpleTestCase

from users import email_codes


class VerifyOnceTests(SimpleTestCase):
    def test_two_requests_that_both_read_the_code_before_either_uses_it_succeed_once(self):
        ident = f'race-{uuid.uuid4().hex}'
        email_codes.issue('signup', ident, 'race@example.com', payload={'k': 'v'})
        code = re.search(r'\b(\d{6})\b', mail.outbox[-1].body).group(1)

        # Jarıs aralıǵı: eki soraw da birinshisi alıp taslamastan aldın tiri kodtı oqıp bolǵan. Haqıyqıy cache
        # (Redis) júklemede bul aralıqtı ózi ashadı; barrier bul jerde onı anıq etedi.
        both_have_read = threading.Barrier(2)
        outcomes = []

        def attempt():
            # Django hár thread ke óz cache obyektin beredi, sol sebepli patch thread tiń ishinde islenwi kerek.
            real_get = email_codes.cache.get

            def get_then_wait(key, *args):
                entry = real_get(key, *args)
                if key == email_codes.entry_key('signup', ident) and entry is not None:
                    both_have_read.wait(timeout=10)
                return entry

            with mock.patch.object(email_codes.cache, 'get', side_effect=get_then_wait):
                outcomes.append(email_codes.verify('signup', ident, code))

        workers = [threading.Thread(target=attempt) for _ in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=30)

        assert len(outcomes) == 2
        assert sum(1 for outcome in outcomes if outcome is not None) == 1
