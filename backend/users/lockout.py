"""
Parol kirisiwi ushın kirisiw lockout siyasatı.

Qátelikler (akkaunt, klient IP) hám akkaunt boyınsha sanaladı:

- Bir IP den 5 qátelik sol IP di sol akkauntqa 30 minutqa bloklaydı.
  Birewdiń akkauntın urıp atırǵan hújimshi tek ózin bloklaydı; iye
  óz tarmaǵınan ele kire aladı.
- Barlıq IP lerden 20 qátelik (30 minutlıq oyna ishinde) akkauntti 15 minutqa
  bloklaydı, tarqalǵan boljawdı sekinletiw ushın.

IP boyınsha qaǵıyda sanaǵıshları keshte turadı (production ta Redis).
"""
from django.core.cache import cache

from common.request import network_key
from common.security_log import log_security_event

IP_FAILURE_LIMIT = 5
IP_LOCK_SECONDS = 30 * 60


def _ip_key(user, client_ip):
    return f'auth_failures:{user.pk}:{network_key(client_ip) or "unknown"}'


def is_locked(user, client_ip):
    """Bul akkaunt bloklanǵan bolsa True, hámmege yamasa usı klient IP ge."""
    if user.is_account_locked():
        return True
    return (cache.get(_ip_key(user, client_ip)) or 0) >= IP_FAILURE_LIMIT


def record_failure(user, client_ip):
    """Usı akkaunt hám IP ushın sátsiz parol urınıwın sanaw."""
    key = _ip_key(user, client_ip)
    cache.add(key, 0, IP_LOCK_SECONDS)
    try:
        failures = cache.incr(key)
    except ValueError:
        # add() hám incr() arasında múddeti ótti
        cache.set(key, 1, IP_LOCK_SECONDS)
        failures = 1
    was_locked = user.is_account_locked()
    user.increment_failed_login()
    # Bir márte, blok baslanǵan waqıtta log qa jazıladı, sol sebepli eskertiw onı kilt etip ala aladı
    if failures == IP_FAILURE_LIMIT:
        log_security_event('lockout', user=user, ip=client_ip, scope='ip')
    if user.is_account_locked() and not was_locked:
        log_security_event('lockout', user=user, ip=client_ip, scope='account')


def record_success(user, client_ip):
    """Tabıslı kirisiwden keyin qátelik sanaǵıshların tazalaw."""
    cache.delete(_ip_key(user, client_ip))
    user.reset_failed_login()
