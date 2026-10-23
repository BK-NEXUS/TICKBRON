"""The account's own thread: read it (polled), write to the team, mark it read, count what is unread."""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from chat import service
from chat.serializers import MessageInputSerializer, MessageSerializer
from chat.service import ChatError
from chat.throttles import ChatPollThrottle, ChatSendThrottle


def after_param(request):
    """`?after=` is the id of the last message the page already has; 0 when absent. None when it is not a number."""
    raw = request.query_params.get('after')
    if raw in (None, ''):
        return 0
    return int(raw) if raw.isascii() and raw.isdigit() else None


def bad_after():
    return Response({'error': 'after must be a message id', 'code': 'invalid_query'}, status=status.HTTP_400_BAD_REQUEST)


def chat_error(exc):
    return Response({'error': exc.message, 'code': exc.code}, status=status.HTTP_400_BAD_REQUEST)


class MyMessages(APIView):
    """GET: the account's thread (the last 100 messages, or only those after `?after=`). POST `{text}`: write to the team."""
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        return [ChatSendThrottle()] if self.request.method == 'POST' else [ChatPollThrottle()]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        after = after_param(request)
        if after is None:
            return bad_after()
        conversation = service.conversation_of(request.user)
        messages = service.messages_after(conversation, after) if conversation else []
        return Response({'messages': MessageSerializer(messages, many=True).data,
                         'unread': service.unread_for_user(request.user)})

    @extend_schema(request=MessageInputSerializer, responses=MessageSerializer)
    def post(self, request):
        data = MessageInputSerializer(data=request.data)
        if not data.is_valid():
            return Response(data.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            message = service.post_from_user(request.user, data.validated_data['text'])
        except ChatError as exc:
            return chat_error(exc)
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class MyRead(APIView):
    """POST: the account has seen the thread."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChatPollThrottle]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        conversation = service.conversation_of(request.user)
        if conversation:
            service.mark_read(conversation, staff=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyUnread(APIView):
    """GET: how many messages from the team the account has not read (the badge)."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChatPollThrottle]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response({'unread': service.unread_for_user(request.user)})
