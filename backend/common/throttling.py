"""Throttles that count a visitor by network block (see common.request.network_key), not by single address."""
from rest_framework.throttling import AnonRateThrottle

from common.request import network_key


class BlockAnonRateThrottle(AnonRateThrottle):
    """DRF's anonymous throttle, with an IPv6 visitor counted by its /64 block."""

    def get_ident(self, request):
        return network_key(super().get_ident(request))
