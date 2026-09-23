"""
Request helpers shared across apps.
"""
import ipaddress

from django.conf import settings


def get_client_ip(request):
    """
    Return the client IP address, trusting X-Forwarded-For only behind known proxies.

    settings.NUM_PROXIES is the number of reverse proxies in front of the app
    that append to X-Forwarded-For. With 0 (the default), the header is
    client-controlled and ignored, and REMOTE_ADDR is used. With N > 0, the
    address N entries from the right is used, which is the one the outermost
    trusted proxy saw; entries further left are whatever the client sent.
    This matches DRF's throttling (REST_FRAMEWORK['NUM_PROXIES']).

    Falls back to REMOTE_ADDR if the chosen value is not a valid IP address.
    """
    remote_addr = request.META.get('REMOTE_ADDR')
    num_proxies = getattr(settings, 'NUM_PROXIES', 0) or 0
    if num_proxies <= 0:
        return remote_addr

    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    addresses = [address.strip() for address in forwarded_for.split(',') if address.strip()]
    if not addresses:
        return remote_addr

    candidate = addresses[-min(num_proxies, len(addresses))]
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return remote_addr
    return candidate
