"""Kelwshini jeke mánzil boyınsha emes, tarmaq bloǵı boyınsha sanaytuǵın throttle ler (qarań common.request.network_key)."""
from rest_framework.throttling import AnonRateThrottle

from common.request import network_key


class BlockAnonRateThrottle(AnonRateThrottle):
    """DRF tiń anonim throttle i, IPv6 kelwshisi óziniń /64 bloǵı boyınsha sanalǵan."""

    def get_ident(self, request):
        return network_key(super().get_ident(request))
