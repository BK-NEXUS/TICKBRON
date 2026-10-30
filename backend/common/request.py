"""
Request helpers shared across apps.
"""
import ipaddress
from collections.abc import Mapping
from contextvars import ContextVar

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


def network_key(ip):
    """
    What limits and lockouts count a client by: the address for IPv4, the /64 block for IPv6.

    A home or phone connection gets a whole /64 from its provider and can switch address inside it
    at will, so counting single IPv6 addresses would let one visitor dodge every limit. An IPv4
    address written as IPv6 (::ffff:1.2.3.4) is the IPv4 address. Anything that is not an address is
    returned unchanged (it is only a cache key).
    """
    if not ip:
        return ip
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return ip
    if address.version == 6:
        if address.ipv4_mapped:
            return str(address.ipv4_mapped)
        return str(ipaddress.ip_network(f'{address}/64', strict=False))
    return str(address)


def object_body(request):
    """The JSON object a client sent, or {} when it sent something else (a list, a text, a number).

    Views read single fields from the body; `request.data.get` on a list is a 500 instead of the 400 the caller earns.
    """
    return request.data if isinstance(request.data, Mapping) else {}


# The address of the request being handled, set by RequestLoggingMiddleware, so code far from the
# view (audit rows) can record where an action came from without every caller passing the request.
_current_ip = ContextVar('current_client_ip', default=None)


def set_current_ip(ip):
    """Remember the client address for this request; returns the token for reset_current_ip."""
    return _current_ip.set(ip)


def reset_current_ip(token):
    _current_ip.reset(token)


def current_ip():
    """The client address of the request being handled, or None outside a request (Celery, shell)."""
    return _current_ip.get()
