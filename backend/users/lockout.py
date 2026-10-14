"""
Login lockout policy shared by password and phone-OTP login.

Failures are counted per (account, client IP) and per account:

- 5 failures from one IP lock that IP out of that account for 30 minutes.
  An attacker hammering someone's account only locks themselves out; the
  owner can still sign in from their own network.
- 20 failures across all IPs (within a 30-minute window) lock the account
  for 15 minutes, to slow down distributed guessing.

Counters for the per-IP rule live in the cache (Redis in production).
"""
from django.core.cache import cache

from common.security_log import log_security_event

IP_FAILURE_LIMIT = 5
IP_LOCK_SECONDS = 30 * 60


def _ip_key(user, client_ip):
    return f'auth_failures:{user.pk}:{client_ip or "unknown"}'


def is_locked(user, client_ip):
    """True if this account is locked, either for everyone or for this client IP."""
    if user.is_account_locked():
        return True
    return (cache.get(_ip_key(user, client_ip)) or 0) >= IP_FAILURE_LIMIT


def record_failure(user, client_ip):
    """Count a failed password/OTP attempt for this account and IP."""
    key = _ip_key(user, client_ip)
    cache.add(key, 0, IP_LOCK_SECONDS)
    try:
        failures = cache.incr(key)
    except ValueError:
        # Expired between add() and incr()
        cache.set(key, 1, IP_LOCK_SECONDS)
        failures = 1
    was_locked = user.is_account_locked()
    user.increment_failed_login()
    # Logged once, at the moment the lock starts, so an alert can key on it
    if failures == IP_FAILURE_LIMIT:
        log_security_event('lockout', user=user, ip=client_ip, scope='ip')
    if user.is_account_locked() and not was_locked:
        log_security_event('lockout', user=user, ip=client_ip, scope='account')


def record_success(user, client_ip):
    """Clear failure counters after a successful login."""
    cache.delete(_ip_key(user, client_ip))
    user.reset_failed_login()
