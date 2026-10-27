from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from chat.models import Conversation, Message
from chat.service import MAX_TEXT


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'text', 'from_staff', 'created_at']
        read_only_fields = fields


class MessageInputSerializer(serializers.Serializer):
    # Length and content are checked by chat.service.clean_text (one place), this only needs a string
    text = serializers.CharField(max_length=MAX_TEXT * 2, allow_blank=True, trim_whitespace=False)


class InboxRowSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread = serializers.IntegerField(read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'user', 'last_message', 'unread', 'last_message_at']
        read_only_fields = fields

    @extend_schema_field(serializers.DictField())
    def get_user(self, obj):
        user = obj.user
        role = user.role.name if user.role_id else ''
        return {
            'id': user.pk,
            'name': user.get_full_name() or user.email,
            'email': user.email,
            'role': 'hotel-owner' if role == 'hotel-owner' else 'customer',
        }

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_last_message(self, obj):
        last = obj.messages.order_by('-id').first()
        if last is None:
            return None
        return {'text': last.text[:120], 'from_staff': last.from_staff, 'created_at': last.created_at}
