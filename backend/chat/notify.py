"""Notices of the support chat (e-mail to the user or the team, Telegram to the team). They carry a link, never the text of the message."""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from chat.models import Message, SmsDelivery
from common.alerts import alerts_configured
from common.sms import send_sms

logger = logging.getLogger(__name__)

SMS_LIMIT_ALERT_KEY = 'chat-sms-limit-alert'
SMS_LIMIT_ALERT_EVERY_SECONDS = 6 * 3600

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


def _tell_team_sms_limit_reached():
    """One Telegram alert per few hours, so a busy day shows the team what happened without a flood."""
    if not alerts_configured() or not cache.add(SMS_LIMIT_ALERT_KEY, 1, SMS_LIMIT_ALERT_EVERY_SECONDS):
        return
    try:
        from common.tasks import send_telegram_message
        send_telegram_message.delay(f'TICKBRON: the daily SMS limit ({settings.SMS_DAILY_LIMIT}) is reached, no more SMS until it clears.')
    except Exception:
        logger.exception('Could not queue the SMS limit alert')


def _within_sms_limits(user):
    """The cost guard: a site-wide cap, a cap per user and a gap between two SMS to the same user (rolling 24 hours)."""
    now = timezone.now()
    day_ago = now - timedelta(hours=24)
    sent = SmsDelivery.objects.filter(status=SmsDelivery.SENT, created_at__gte=day_ago)
    if sent.count() >= settings.SMS_DAILY_LIMIT:
        _tell_team_sms_limit_reached()
        return False
    mine = sent.filter(user=user)
    if mine.count() >= settings.SMS_PER_USER_PER_DAY:
        return False
    return not mine.filter(created_at__gte=now - timedelta(minutes=settings.SMS_MIN_GAP_MINUTES)).exists()


def sms_recipient(message):
    """The user to text about a new staff reply, or None. The user must have agreed and have a number."""
    if not settings.SMS_ENABLED or not message.from_staff or not _first_unread(message):
        return None
    user = message.conversation.user
    if not (user.is_active and user.sms_notifications and user.phone_number):
        return None
    return user if _within_sms_limits(user) else None


def send_reply_sms(message):
    """Text the user that the team answered: a fixed line with a link, never the message text. A failing provider is only recorded."""
    user = sms_recipient(message)
    if user is None:
        return
    try:
        send_sms(user.phone_number, f'TICKBRON: sizga yangi xabar bor. {settings.FRONTEND_URL}/support')
        status = SmsDelivery.SENT
    except Exception:
        logger.exception('SMS for chat message %s failed', message.pk)
        status = SmsDelivery.FAILED
    SmsDelivery.objects.create(user=user, kind=SmsDelivery.CHAT_REPLY, status=status)


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
    send_reply_sms(message)
