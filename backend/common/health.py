"""
Liveness and readiness probes for a load balancer or uptime monitor.

/healthz/  the process answers.
/readyz/   the database and the cache (Redis in production: throttles and lockouts live there)
           both work. Failures answer 503 with no detail, since the endpoints are public.
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
