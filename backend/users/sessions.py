"""Starting a signed-in session after a successful password or SMS login."""
import logging

from django.contrib.auth import login

from accounts.history import record_history
from common.security_log import log_security_event
from users import lockout


def start_session(request, user, client_ip, method):
    """Clear the failure counters, remember the IP, sign the user in and write the event and history row."""
    lockout.record_success(user, client_ip)
    user.last_login_ip = client_ip
    user.save(update_fields=['last_login_ip'])
    login(request, user)
    log_security_event('login_success', request, user=user, level=logging.INFO, method_used=method)
    record_history(user, 'login', request)
