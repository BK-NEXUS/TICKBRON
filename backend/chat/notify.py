"""Notices of the support chat (e-mail to the user or the team, Telegram to the team). They carry a link, never the text of the message."""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from chat.models import Message
from common.alerts import alerts_configured

logger = logging.getLogger(__name__)

USER_SUBJECT = 'TICKBRON: yangi xabar / новое сообщение / new message'
TEAM_SUBJECT = 'TICKBRON support: new message'


def _first_unread(message):
    """True when no earlier message of the same side is still unread, so a run of messages sends one notice."""
    conversation = message.conversation
    if message.from_staff:
        read_id = conversation.user_read_id
    else:
        read_id = conversation.staff_read_id
    unread = Message.objects.filter(
        conversation=conversation, from_staff=message.from_staff, pk__gt=read_id, pk__lte=message.pk).count()
    return unread == 1


def notice_for(message):
    """(subject, body, recipient) for a new message, or None when nobody has to be told."""
    if not _first_unread(message):
        return None
    user = message.conversation.user
    if message.from_staff:
        if not user.is_active or not user.email:
            return None
        body = render_to_string('chat/notice_to_user.txt', {'link': f'{settings.FRONTEND_URL}/support'})
        return USER_SUBJECT, body, user.email
    if not settings.SUPPORT_NOTIFY_EMAIL:
        return None
    body = render_to_string('chat/notice_to_team.txt', {
        'name': user.full_name or user.email, 'email': user.email,
        'role': user.role.name if user.role else 'guest', 'link': f'{settings.FRONTEND_URL}/admin'})
    return TEAM_SUBJECT, body, settings.SUPPORT_NOTIFY_EMAIL


def telegram_text_for(message):
    """The Telegram text for the team when a user writes (name and role, no address and no message text), else None."""
    if message.from_staff or not alerts_configured() or not _first_unread(message):
        return None
    user = message.conversation.user
    role = user.role.name if user.role else 'guest'
    return f'TICKBRON support: new message from {user.full_name or "a user"} ({role})\n{settings.FRONTEND_URL}/admin'


def send_notice(message):
    """Tell the team on Telegram, then mail: a broken Telegram queue must not stop the e-mail."""
    text = telegram_text_for(message)
    if text:
        try:
            from common.tasks import send_telegram_message
            send_telegram_message.delay(text)
        except Exception:
            logger.exception('Could not queue the Telegram notice for message %s', message.pk)
    notice = notice_for(message)
    if notice:
        subject, body, recipient = notice
        send_mail(subject, body, None, [recipient])
