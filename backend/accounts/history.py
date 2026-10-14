"""The user-visible account history (logins, logout, sign-up) written from the auth views."""
import logging

from django.db import transaction

from accounts.models import AccountHistory
from common.request import get_client_ip

logger = logging.getLogger(__name__)
MAX_USER_AGENT_LENGTH = 500


def record_history(user, action, request):
    """Add one AccountHistory row; a failure is logged and never breaks the login itself."""
    try:
        with transaction.atomic():
            AccountHistory.objects.create(
                user=user, action=action, ip_address=get_client_ip(request),
                user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:MAX_USER_AGENT_LENGTH],
            )
    except Exception:
        logger.exception('Could not write the %s history entry for user %s', action, user.pk)
