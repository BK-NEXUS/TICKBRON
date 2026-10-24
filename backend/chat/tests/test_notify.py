"""E-mail notices of the support chat: one per unread run, with a link and without the message text."""
from unittest import mock

import pytest
from django.core import mail
from django.test import override_settings
from rest_framework.test import APIClient

from chat import service
from chat.models import Conversation
from chat.tasks import send_chat_notice
from users.models import User

pytestmark = pytest.mark.django_db
TEAM_INBOX = 'support@tickbron.test'
SECRET = 'my private question about room 12'


@pytest.fixture(autouse=True)
def run_tasks_at_once():
    """The task normally runs in a worker; here it runs when it is queued."""
    with mock.patch('chat.tasks.send_chat_notice.delay', side_effect=lambda message_id: send_chat_notice.run(message_id)):
        yield


@pytest.fixture
def guest():
    return User.objects.create_user(email='guest@example.com', password='Pass12345!', full_name='Aziz Karimov')


@pytest.fixture
def staff():
    return User.objects.create_user(email='staff@example.com', password='Pass12345!', full_name='Staff', is_staff=True)


def write(user, text, capture):
    with capture(execute=True):
        return service.post_from_user(user, text)


def reply(conversation, staff_user, text, capture):
    with capture(execute=True):
        return service.post(conversation=conversation, sender=staff_user, text=text, from_staff=True)


def test_a_reply_mails_the_user_with_a_link_and_without_the_text(guest, staff, django_capture_on_commit_callbacks):
    write(guest, 'Hello', django_capture_on_commit_callbacks)
    conversation = Conversation.objects.get(user=guest)
    mail.outbox.clear()
    reply(conversation, staff, SECRET, django_capture_on_commit_callbacks)
    assert [m.to for m in mail.outbox] == [['guest@example.com']]
    assert '/support' in mail.outbox[0].body
    assert SECRET not in mail.outbox[0].body and SECRET not in mail.outbox[0].subject


def test_a_second_reply_while_the_first_is_unread_sends_nothing(guest, staff, django_capture_on_commit_callbacks):
    write(guest, 'Hello', django_capture_on_commit_callbacks)
    conversation = Conversation.objects.get(user=guest)
    mail.outbox.clear()
    reply(conversation, staff, 'one', django_capture_on_commit_callbacks)
    reply(conversation, staff, 'two', django_capture_on_commit_callbacks)
    assert len(mail.outbox) == 1


def test_a_reply_after_the_user_read_the_thread_mails_again(guest, staff, django_capture_on_commit_callbacks):
    write(guest, 'Hello', django_capture_on_commit_callbacks)
    conversation = Conversation.objects.get(user=guest)
    mail.outbox.clear()
    reply(conversation, staff, 'one', django_capture_on_commit_callbacks)
    service.mark_read(conversation, staff=False)
    reply(conversation, staff, 'two', django_capture_on_commit_callbacks)
    assert len(mail.outbox) == 2


def test_a_deactivated_user_gets_no_mail(guest, staff, django_capture_on_commit_callbacks):
    write(guest, 'Hello', django_capture_on_commit_callbacks)
    conversation = Conversation.objects.get(user=guest)
    User.objects.filter(pk=guest.pk).update(is_active=False)
    mail.outbox.clear()
    reply(conversation, staff, 'one', django_capture_on_commit_callbacks)
    assert mail.outbox == []


@override_settings(SUPPORT_NOTIFY_EMAIL=TEAM_INBOX)
def test_a_user_message_mails_the_team_inbox_once_per_unread_run(guest, django_capture_on_commit_callbacks):
    write(guest, SECRET, django_capture_on_commit_callbacks)
    write(guest, 'and one more thing', django_capture_on_commit_callbacks)
    assert [m.to for m in mail.outbox] == [[TEAM_INBOX]]
    assert 'guest@example.com' in mail.outbox[0].body
    assert SECRET not in mail.outbox[0].body


@override_settings(SUPPORT_NOTIFY_EMAIL=TEAM_INBOX)
def test_the_team_is_mailed_again_after_it_read_the_thread(guest, django_capture_on_commit_callbacks):
    write(guest, 'one', django_capture_on_commit_callbacks)
    service.mark_read(Conversation.objects.get(user=guest), staff=True)
    write(guest, 'two', django_capture_on_commit_callbacks)
    assert len(mail.outbox) == 2


@override_settings(SUPPORT_NOTIFY_EMAIL='')
def test_without_a_team_inbox_the_team_is_not_mailed(guest, django_capture_on_commit_callbacks):
    write(guest, 'Hello', django_capture_on_commit_callbacks)
    assert mail.outbox == []


def test_a_broken_queue_does_not_stop_the_message(guest, django_capture_on_commit_callbacks):
    with mock.patch('chat.tasks.send_chat_notice.delay', side_effect=ConnectionError('no broker')):
        message = write(guest, 'Hello', django_capture_on_commit_callbacks)
    assert message.pk and Conversation.objects.filter(user=guest).exists()


def test_a_failing_mail_server_does_not_break_the_api(guest, django_capture_on_commit_callbacks):
    client = APIClient()
    client.force_authenticate(user=guest)
    with mock.patch('chat.tasks.send_chat_notice.delay', side_effect=ConnectionError('no broker')):
        with django_capture_on_commit_callbacks(execute=True):
            response = client.post('/api/v1/chat/messages/', {'text': 'Hello'}, format='json')
    assert response.status_code == 201


def test_a_missing_message_is_ignored():
    assert send_chat_notice.run(999999) is None
