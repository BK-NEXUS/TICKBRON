"""The team's side: the inbox, one thread, replies, read marks and the unread badge. Staff and super-admin."""
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_panel.views import IsSuperAdminOrStaff
from chat import service
from chat.models import Conversation
from chat.serializers import InboxRowSerializer, MessageInputSerializer, MessageSerializer
from chat.service import ChatError
from chat.throttles import ChatPollThrottle, ChatSendThrottle
from chat.views import after_param, bad_after, chat_error


class Inbox(APIView):
    """GET: the threads, newest activity first. `?unread=true` keeps those with unread messages, `?q=` searches name or e-mail."""
    permission_classes = [IsSuperAdminOrStaff]
    throttle_classes = [ChatPollThrottle]

    @extend_schema(responses=InboxRowSerializer(many=True))
    def get(self, request):
        threads = service.inbox(
            search=(request.query_params.get('q') or '').strip(),
            unread_only=request.query_params.get('unread') == 'true')
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(threads, request)
        return paginator.get_paginated_response(InboxRowSerializer(page, many=True).data)


class Thread(APIView):
    """GET: one thread (the last 100 messages, or those after `?after=`). POST `{text}`: the team answers."""
    permission_classes = [IsSuperAdminOrStaff]

    def get_throttles(self):
        return [ChatSendThrottle()] if self.request.method == 'POST' else [ChatPollThrottle()]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, conversation_id):
        after = after_param(request)
        if after is None:
            return bad_after()
        conversation = get_object_or_404(Conversation.objects.select_related('user', 'user__role'), pk=conversation_id)
        row = Conversation.objects.filter(pk=conversation.pk).select_related('user', 'user__role').first()
        return Response({
            'user': InboxRowSerializer(row).data['user'],
            'messages': MessageSerializer(service.messages_after(conversation, after), many=True).data,
        })

    @extend_schema(request=MessageInputSerializer, responses=MessageSerializer)
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, pk=conversation_id)
        data = MessageInputSerializer(data=request.data)
        if not data.is_valid():
            return Response(data.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            message = service.post(
                conversation=conversation, sender=request.user, text=data.validated_data['text'], from_staff=True)
        except ChatError as exc:
            return chat_error(exc)
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class ThreadRead(APIView):
    """POST: the team has read the thread."""
    permission_classes = [IsSuperAdminOrStaff]
    throttle_classes = [ChatPollThrottle]

    @extend_schema(request=None, responses={204: None})
    def post(self, request, conversation_id):
        service.mark_read(get_object_or_404(Conversation, pk=conversation_id), staff=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class StaffUnread(APIView):
    """GET: how many threads have messages the team has not read (the badge on the admin tab)."""
    permission_classes = [IsSuperAdminOrStaff]
    throttle_classes = [ChatPollThrottle]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response({'unread_threads': service.unread_threads_for_staff()})
