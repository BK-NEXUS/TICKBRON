"""
TICKBRON Backend ushın óz decorator ları.

Rate limit, keshlew hám basqa járdemshi decorator lardı usınadı.
"""
from django.core.cache import cache
from common.request import get_client_ip as _get_client_ip
from common.request import network_key
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from functools import wraps
import logging

logger = logging.getLogger('tickbron')


def rate_limit(limit='100/h', key_func=None):
    """
    API endpoint leri ushın rate limit decorator ı.

    Argumentler:
        limit: Rate limit qatarı (mısalı '100/h', '1000/d', '10/m')
        key_func: Kesh kiltin jasaytuǵın funkciya (ádetde paydalanıwshı ID si yamasa IP)

    Paydalanıw:
        @rate_limit('100/h')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Kesh kiltin jasaw
            if key_func:
                cache_key = key_func(request)
            elif request.user.is_authenticated:
                cache_key = f"rate_limit:{request.user.id}"
            else:
                cache_key = f"rate_limit:{network_key(get_client_ip(request))}"

            # Limit ti oqıw (mısalı '100/h' -> saatına 100 soraw)
            try:
                count, period = limit.split('/')
                count = int(count)
                period_seconds = {
                    's': 1,
                    'm': 60,
                    'h': 3600,
                    'd': 86400
                }.get(period.lower(), 3600)
            except (ValueError, AttributeError):
                logger.error(f"Invalid rate limit format: {limit}")
                count = 100
                period_seconds = 3600

            # Rate limit ti tekseriw
            current_count = cache.get(cache_key, 0)

            if current_count >= count:
                logger.warning(f"Rate limit exceeded for {cache_key}")
                raise PermissionDenied("Rate limit exceeded. Please try again later.")

            # Sanaǵıshtı arttırıw
            cache.set(cache_key, current_count + 1, period_seconds)

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


def get_client_ip(request):
    """Sorawdan klient IP mánzilin alıw."""
    return _get_client_ip(request)


def class_rate_limit(limit='100/h', key_func=None):
    """
    Class tiykarlı view ler ushın rate limit decorator ı.

    Paydalanıw:
        @class_rate_limit('100/h')
        class MyView(View):
            ...
    """
    return method_decorator(rate_limit(limit, key_func), name='dispatch')
