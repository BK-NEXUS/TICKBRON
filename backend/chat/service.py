"""All chat rules live here; views only call these functions."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Exists, F, OuterRef, Q
from django.utils import timezone

from chat.models import Conversation, Message
from common.validators import validate_free_text

MAX_TEXT = 2000
PAGE = 100  # messages in one answer; a thread is read from the end


class ChatError(Exception):
    """A rule was broken. `code` is a stable name the API returns; `message` is for people."""

    def __init__(self, code, message=''):
        super().__init__(message or code)
        self.code = code
        self.message = message or code


def clean_text(raw):
    text = (raw or '').strip()
    if not text:
        raise ChatError('empty', 'Write a message first')
    if len(text) > MAX_TEXT:
        raise ChatError('too_long', f'A message is at most {MAX_TEXT} characters')
    try:
        validate_free_text(text)
    except ValidationError as exc:
        raise ChatError('bad_text', exc.messages[0]) from exc
    return text


def conversation_of(user):
    """The account's own thread, created at the first message."""
    return Conversation.objects.filter(user=user).first()


def post(*, conversation, sender, text, from_staff):
    """Add one message to a thread (the thread's own `last_message_at` and the sender's read mark follow)."""
    text = clean_text(text)
    with transaction.atomic():
        message = Message.objects.create(conversation=conversation, sender=sender, from_staff=from_staff, text=text)
        read_field = 'staff_read_id' if from_staff else 'user_read_id'
        Conversation.objects.filter(pk=conversation.pk).update(
            last_message_at=message.created_at, **{read_field: message.pk})
    return message


def post_from_user(user, text):
    """A guest or owner writes to the team; the thread is created on the first message."""
    text = clean_text(text)
    with transaction.atomic():
        conversation, _ = Conversation.objects.get_or_create(user=user, defaults={'last_message_at': timezone.now()})
        return post(conversation=conversation, sender=user, text=text, from_staff=False)


def messages_after(conversation, after_id=0):
    """New messages after `after_id`; the first read (after_id 0) gives the last PAGE ones, oldest first."""
    queryset = Message.objects.filter(conversation=conversation)
    if after_id:
        return list(queryset.filter(pk__gt=after_id).order_by('id')[:PAGE])
    return list(reversed(list(queryset.order_by('-id')[:PAGE])))


def mark_read(conversation, *, staff):
    newest = Message.objects.filter(conversation=conversation).order_by('-id').values_list('pk', flat=True).first() or 0
    field = 'staff_read_id' if staff else 'user_read_id'
    # Never moves backwards, even when two readers race
    Conversation.objects.filter(pk=conversation.pk, **{f'{field}__lt': newest}).update(**{field: newest})


def unread_for_user(user):
    """Messages from the team the account has not read yet."""
    return Message.objects.filter(
        conversation__user=user, from_staff=True, pk__gt=F('conversation__user_read_id')).count()


def _unseen_by_staff():
    return Message.objects.filter(
        conversation=OuterRef('pk'), from_staff=False, pk__gt=OuterRef('staff_read_id'))


def inbox(*, search='', unread_only=False):
    """Threads for the admin screen, newest activity first, with how many messages the team has not read."""
    queryset = Conversation.objects.select_related('user', 'user__role').annotate(
        unread=Count('messages', filter=Q(messages__from_staff=False, messages__pk__gt=F('staff_read_id'))))
    if search:
        queryset = queryset.filter(
            Q(user__full_name__icontains=search) | Q(user__email__icontains=search)
            | Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search))
    if unread_only:
        queryset = queryset.filter(Exists(_unseen_by_staff()))
    return queryset.order_by('-last_message_at', '-id')


def unread_threads_for_staff():
    """How many threads have a message the team has not read (the badge on the admin tab)."""
    return Conversation.objects.filter(Exists(_unseen_by_staff())).count()
