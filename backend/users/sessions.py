"""Tabıslı parol kirisiwinen keyin kirgen session di baslaw."""
import logging

from django.contrib.auth import login

from accounts.history import record_history
from common.security_log import log_security_event
from users import lockout


def start_session(request, user, client_ip, method):
    """Qátelik sanaǵıshların tazalaw, IP di esinde saqlaw, paydalanıwshını kirgiziw hám waqıya hám tariyx qatarın jazıw."""
    lockout.record_success(user, client_ip)
    user.last_login_ip = client_ip
    user.save(update_fields=['last_login_ip'])
    login(request, user)
    log_security_event('login_success', request, user=user, level=logging.INFO, method_used=method)
    record_history(user, 'login', request)
