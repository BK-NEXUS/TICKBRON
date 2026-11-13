"""
Load balancer yamasa uptime monitor ushın liveness hám readiness tekseriwleri.

/healthz/  process juwap beredi.
/readyz/   database hám kesh (production ta Redis: throttle hám lockout lar sonda turadı)
           ekewi de isleydi. Qátelikte 503 beredi, tolıq maǵlıwmatsız, sebebi endpoint ler ashıq.
"""
import logging

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def healthz(request):
    return JsonResponse({'status': 'ok'})


def readyz(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        cache.set('readyz', '1', 10)
        if cache.get('readyz') != '1':
            raise RuntimeError('cache did not return what was stored')
    except Exception:
        logger.exception('Readiness check failed')
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})
