"""
Hár kelwshi birdey alatuǵın juwaplardıń qısqa múddetli nusqası: mehmanxana beti, bos orınlar, izlew nátiyjeleri hám
izlew filter leri. Mıńlaǵan kelwshi birdey birneshe mehmanxananı qarasa, kóp sorawlarǵa database emes
Redis juwap beredi. (.ai/LOAD_TEST.md)

- Tek kim sorawına baylanıslı bolmaǵan juwaplar ushın. Juwap PUBLIC_CACHE_SECONDS saqlanadı (0 onı óshiredi), sol sebepli
  dizimdegi baha yamasa bos xona sanı sonsha sekund eski bolıwı múmkin; bronlaw hárdayım qayta tekseredi.
- Hesh qashan qátelik juwabı emes: `build` qátelik kóteredi yamasa view `remember` di shaqırmastan juwap beredi.
- Óship turǵan kesh hesh qashan bettiń sátsiz bolıwına sebep emes: juwap kesh joq sıyaqlı qurıladı.
- Tólengen banner ler hám olardıń kóriw sanaǵıshı nusqalanǵan juwaptıń bólegi emes; olardı qurǵan view ler hár soraw ushın
qaladı.
"""
import hashlib
import logging
import time

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('tickbron')

KEY_PREFIX = 'public'
# Óship turǵan kesh server qálegen shaqırıwǵa tek timeout ten keyin juwap beredi: sátsizlikten keyin keshke usı waqıt tiyilmeydi
PAUSE_SECONDS = 15
_paused_until = 0.0
# Usıdan úlken bir juwap sonday ólshemdegi Redis aylanısına tiymeydi
MAX_ITEMS = 2000


def resume():
    global _paused_until
    _paused_until = 0.0


def _pause():
    global _paused_until
    _paused_until = time.monotonic() + PAUSE_SECONDS


def _paused():
    return time.monotonic() < _paused_until


def seconds():
    return max(int(getattr(settings, 'PUBLIC_CACHE_SECONDS', 0)), 0)


def key_for(request, scope):
    """Birdey mánzil, query (qálegen tártipte), til hám host birdey kilt beredi; basqa hesh nárse bermeydi."""
    query = '&'.join(sorted(request.META.get('QUERY_STRING', '').split('&')))
    fingerprint = '\n'.join((scope, request.get_host(), request.path, query, getattr(request, 'LANGUAGE_CODE', '')))
    return f'{KEY_PREFIX}:{scope}:{hashlib.sha256(fingerprint.encode("utf-8", "surrogatepass")).hexdigest()}'


def remember(request, scope, build, divisor=1):
    """`build()` tıń juwabı (ápiwayı maǵlıwmat), jańa nusqa bolsa nusqadan. `divisor` waqıttı qısqartadı."""
    ttl = seconds() // max(divisor, 1)
    if ttl <= 0 or _paused():
        return build()
    key = key_for(request, scope)
    try:
        found = cache.get(key)
    except Exception:
        logger.warning('Public cache read failed; leaving it alone for %s seconds', PAUSE_SECONDS, exc_info=True)
        _pause()
        return build()
    if found is not None:
        return found
    data = build()
    if _small_enough(data):
        try:
            cache.set(key, data, ttl)
        except Exception:
            logger.warning('Public cache write failed; leaving it alone for %s seconds', PAUSE_SECONDS, exc_info=True)
            _pause()
    return data


def _small_enough(data):
    results = data.get('results') if isinstance(data, dict) else None
    return not isinstance(results, list) or len(results) <= MAX_ITEMS
