"""
What an administrator's change of someone's e-mail leaves behind: a masked-and-hashed trace for the
audit row and a notice to the OLD address.
"""
import hashlib
import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string

from users import email_codes

logger = logging.getLogger(__name__)

EMAIL_SUBJECT = 'TICKBRON: e-mail o\'zgartirildi / e-mail изменён / e-mail changed'


def audit_trace(email):
    """"o***@gmail.com#1a2b3c4d5e6f": recognisable by a person, comparable by hash, useless to an attacker."""
    digest = hashlib.sha256(email.lower().encode()).hexdigest()[:12]
    return f'{email_codes.hint(email)}#{digest}'


def send_change_notice(old_email, new_email):
    """Tell the old mailbox the address was changed, so a takeover does not go unnoticed. A mail failure must not undo the change."""
    body = render_to_string('users/email_changed_email.txt', {'new_hint': email_codes.hint(new_email)})
    try:
        send_mail(EMAIL_SUBJECT, body, None, [old_email])
    except Exception:
        logger.exception('Could not send the e-mail change notice')
