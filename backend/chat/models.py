"""
Chat between one account and the TICKBRON team (.ai/PLAN_SUPPORT_CHAT.md).

One `Conversation` per account (a guest or a hotel owner); the team answers inside it. Each side keeps the id of
the last message it has read, so "unread" is a count of the other side's messages after that id.
"""
from django.conf import settings
from django.db import models


class Conversation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_conversation')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(db_index=True)
    # Id of the newest message each side has seen (0: nothing yet)
    user_read_id = models.BigIntegerField(default=0)
    staff_read_id = models.BigIntegerField(default=0)

    class Meta:
        db_table = 'chat_conversations'
        ordering = ['-last_message_at', '-id']

    def __str__(self):
        return f'Conversation {self.pk} user:{self.user_id}'


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    from_staff = models.BooleanField(default=False)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['id']
        indexes = [models.Index(fields=['conversation', 'id'], name='chat_msg_conv_id_idx')]

    def __str__(self):
        return f'Message {self.pk} conversation:{self.conversation_id}'
