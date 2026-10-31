"""
A short-lived copy of the answers every visitor gets the same: the hotel page, availability, search results and the
search filters. With thousands of visitors looking at the same few hotels, most requests are answered from Redis
instead of the database. (.ai/LOAD_TEST.md)

- Only for answers that do not depend on who asks. The answer is kept for PUBLIC_CACHE_SECONDS (0 turns it off), so a
  price or a free-room count on a listing can be that many seconds old; booking always checks again.
- Never an error answer: `build` raises or the view answers without calling `remember`.
- A cache that is down is never a reason for a page to fail: the answer is then built as if there were no cache.
- The paid banners and their view counter are not part of a copied answer; the views that build them stay per request.
"""
import hashlib
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('tickbron')

KEY_PREFIX = 'public'
# A single answer bigger than this is not worth a Redis round trip of that size
MAX_ITEMS = 2000


def seconds():
    return max(int(getattr(settings, 'PUBLIC_CACHE_SECONDS', 0)), 0)


def key_for(request, scope):
    """The same address, query (in any order), language and host give the same key; nothing else does."""
    query = '&'.join(sorted(request.META.get('QUERY_STRING', '').split('&')))
    fingerprint = '\n'.join((scope, request.get_host(), request.path, query, getattr(request, 'LANGUAGE_CODE', '')))
    return f'{KEY_PREFIX}:{scope}:{hashlib.sha256(fingerprint.encode("utf-8", "surrogatepass")).hexdigest()}'


def remember(request, scope, build, divisor=1):
    """The answer of `build()` (plain data), from the copy when there is a fresh one. `divisor` shortens the time."""
    ttl = seconds() // max(divisor, 1)
    if ttl <= 0:
        return build()
    key = key_for(request, scope)
    try:
        found = cache.get(key)
    except Exception:
        logger.warning('Public cache read failed', exc_info=True)
        found = None
    if found is not None:
        return found
    data = build()
    if _small_enough(data):
        try:
            cache.set(key, data, ttl)
        except Exception:
            logger.warning('Public cache write failed', exc_info=True)
    return data


def _small_enough(data):
    results = data.get('results') if isinstance(data, dict) else None
    return not isinstance(results, list) or len(results) <= MAX_ITEMS
