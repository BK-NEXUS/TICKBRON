"""
One place for security events: who did what, from where, and how it ended.

Lines go to the `tickbron.security` logger, which production keeps at INFO in its own file
(config/logging_config.py), so an investigation does not depend on the general log level.
A line is `event=<name> user=<id|none> ip=<address> method=<GET> path=<url> key=value ...`.
Only ids, addresses and fixed reason codes are written: never an e-mail, phone number,
password, one-time code or token. Caller-chosen text is escaped so it cannot forge a line.
"""
import logging

from common.middleware import printable
from common.request import get_client_ip

security_logger = logging.getLogger('tickbron.security')
MAX_VALUE_LENGTH = 100


def _value(value):
    return printable(value)[:MAX_VALUE_LENGTH]


def log_security_event(event, request=None, user=None, level=logging.WARNING, **fields):
    """Write one security event. `user` defaults to the authenticated user of `request`."""
    if user is None and request is not None and getattr(request, 'user', None) is not None:
        user = request.user if request.user.is_authenticated else None
    parts = [f'event={event}', f'user={user.pk if user is not None else "none"}']
    if request is not None:
        fields.setdefault('ip', get_client_ip(request))
        parts += [f'ip={_value(fields.pop("ip"))}', f'method={_value(request.method)}', f'path={_value(request.path)}']
    parts += [f'{key}={_value(value)}' for key, value in fields.items()]
    security_logger.log(level, ' '.join(parts))
