"""
App lar ortaq paydalanatuǵın request járdemshileri.
"""
import ipaddress
from collections.abc import Mapping
from contextvars import ContextVar

from django.conf import settings


def get_client_ip(request):
    """
    Klient IP mánzilin qaytaradı, X-Forwarded-For ga tek belgili proxy lerdiń artında isenedi.

    settings.NUM_PROXIES app aldındaǵı X-Forwarded-For ge qosatuǵın
    reverse proxy ler sanı. 0 (ádetde) bolsa, header
    klient basqaradı hám itibarǵa alınbaydı, REMOTE_ADDR paydalanıladı. N > 0 bolsa,
    oń jaqtan N-shi jazba paydalanıladı, ol eń sırtqı isenimli
    proxy kórgen mánzil; shepte kóbirek jazbalar klient jibergen nárse.
    Bul DRF tiń throttling i menen sáykes keledi (REST_FRAMEWORK['NUM_PROXIES']).

    Tańlanǵan mánis jaramlı IP mánzil bolmasa REMOTE_ADDR ge qaytadı.
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
    Limit ler hám lockout lar klientti nege qarap sanaydı: IPv4 ushın mánzil, IPv6 ushın /64 blok.

    Úy yamasa telefon baylanısı provayderinen pútkil /64 aladı hám onıń ishinde mánzildi
    qálegen waqıtta almastıra aladı, sol sebepli jeke IPv6 mánzillerdi sanaw bir kelwshige hár limit ten qutılıwǵa
    múmkinshilik berer edi. IPv6 retinde jazılǵan IPv4 mánzil (::ffff:1.2.3.4) IPv4 mánzil. Mánzil bolmaǵan hár nárse
    ózgerissiz qaytarıladı (ol tek kesh kilti).
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
    """Klient jibergen JSON obyekti, yamasa basqa nárse (dizim, tekst, san) jiberse {}.

    View ler denedegi jeke maydanlardı oqıydı; dizimde `request.data.get` shaqırıwdan shaqırıwshı layıq 400 emes 500 aladı.
    """
    return request.data if isinstance(request.data, Mapping) else {}


# RequestLoggingMiddleware belgilegen, islenip atırǵan sorawdıń mánzili, sonda view den uzaq kod
# (audit qatarları) hár shaqırıwshı sorawdı bermesten háreket qayaqtan kelgenin jaza aladı.
_current_ip = ContextVar('current_client_ip', default=None)


def set_current_ip(ip):
    """Usı soraw ushın klient mánzilin esinde saqlaw; reset_current_ip ushın token qaytaradı."""
    return _current_ip.set(ip)


def reset_current_ip(token):
    _current_ip.reset(token)


def current_ip():
    """Islenip atırǵan sorawdıń klient mánzili, yamasa soraw sırtında (Celery, shell) None."""
    return _current_ip.get()
