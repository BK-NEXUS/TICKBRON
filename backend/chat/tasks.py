from celery import shared_task

from chat.models import Message
from chat.notify import send_notice


@shared_task
def send_chat_notice(message_id):
    """Jańa xabar xabarlandırıwın e-mail ge jiberiw. Xabarǵa bul isleniwden aldın juwap berilgen, sol sebepli sekin e-mail
    server hesh nárse kórsetpeydi."""
    message = Message.objects.select_related('conversation__user__role').filter(pk=message_id).first()
    if message is not None:
        send_notice(message)
