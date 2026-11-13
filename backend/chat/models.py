"""
Bir akkaunt hám TICKBRON komandası arasındaǵı chat (.ai/PLAN_SUPPORT_CHAT.md).

Hár akkaunt (mehmann yamasa mehmanxana iyesi) ushın bir `Conversation`; komanda onıń ishinde juwap beredi. Hár tárep óz
oqıǵan
sońǵı xabarınıń id sin saqlaydı, sol sebepli "oqılmaǵan" sol id den keyingi basqa tárep xabarlarınıń sanı.
"""
from django.conf import settings
from django.db import models


class Conversation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_conversation')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(db_index=True)
    # Hár tárep kórgen eń jańa xabardıń id si (0: ele joq)
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
