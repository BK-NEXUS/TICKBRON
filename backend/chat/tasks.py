from celery import shared_task

from chat.models import Message
from chat.notify import send_notice


@shared_task
def send_chat_notice(message_id):
    """Mail the notice of a new message. The message was answered before this runs, so a slow mail server shows nothing."""
    message = Message.objects.select_related('conversation__user__role').filter(pk=message_id).first()
    if message is not None:
        send_notice(message)
