"""SMS when the team answers a user: only with the user's consent, a phone number and the switch on;
limited per user and per day; never with the text of the chat in it (plan .ai/PLAN_SMS_CHAT.md)."""
from datetime import timedelta
from unittest import mock

import pytest
from django.core import mail
from django.core.cache import cache
from django.utils import timezone

from chat import service
from chat.models import Conversation, SmsDelivery
from chat.tasks import send_chat_notice
from users.models import User

pytestmark = pytest.mark.django_db
PHONE = '+998901234567'
SECRET = 'my private question about room 12'


@pytest.fixture(autouse=True)
def run_tasks_at_once():
    """The task normally runs in a worker; here it runs when it is queued."""
    with mock.patch('chat.tasks.send_chat_notice.delay', side_effect=lambda message_id: send_chat_notice.run(message_id)):
        yield


@pytest.fixture(autouse=True)
def sms_settings(settings):
    settings.SMS_ENABLED = True
    settings.SMS_PER_USER_PER_DAY = 3
    settings.SMS_MIN_GAP_MINUTES = 10
    settings.SMS_DAILY_LIMIT = 300
    cache.clear()


@pytest.fixture
def sms():
    with mock.patch('chat.notify.send_sms') as fake:
        yield fake


@pytest.fixture
def guest():
    return User.objects.create_user(
        email='guest@example.com', password='Pass12345!', full_name='Aziz Karimov',
        phone_number=PHONE, sms_notifications=True)


@pytest.fixture
def staff():
    return User.objects.create_user(email='staff@example.com', password='Pass12345!', full_name='Staff', is_staff=True)


def write(user, text, capture):
    with capture(execute=True):
        return service.post_from_user(user, text)


def reply(conversation, staff_user, text, capture):
    with capture(execute=True):
        return service.post(conversation=conversation, sender=staff_user, text=text, from_staff=True)


def conversation_after_question(guest, capture):
    write(guest, 'Hello', capture)
    return Conversation.objects.get(user=guest)


def delivered(user, minutes_ago, status=SmsDelivery.SENT):
    row = SmsDelivery.objects.create(user=user, kind=SmsDelivery.CHAT_REPLY, status=status)
    SmsDelivery.objects.filter(pk=row.pk).update(created_at=timezone.now() - timedelta(minutes=minutes_ago))


def test_a_reply_sends_one_sms_with_a_link_and_without_the_text(guest, staff, sms, django_capture_on_commit_callbacks):
    conversation = conversation_after_question(guest, django_capture_on_commit_callbacks)
    reply(conversation, staff, SECRET, django_capture_on_commit_callbacks)
    sms.assert_called_once()
    phone, text = sms.call_args.args
    assert phone == PHONE
    assert '/support' in text and SECRET not in text
    assert SmsDelivery.objects.filter(user=guest, status=SmsDelivery.SENT).count() == 1


def test_a_second_reply_while_the_first_is_unread_sends_no_second_sms(guest, staff, sms, django_capture_on_commit_callbacks):
    conversation = conversation_after_question(guest, django_capture_on_commit_callbacks)
    reply(conversation, staff, 'one', django_capture_on_commit_callbacks)
    reply(conversation, staff, 'two', django_capture_on_commit_callbacks)
    assert sms.call_count == 1


def test_a_message_of_the_user_sends_no_sms(guest, sms, django_capture_on_commit_callbacks):
    write(guest, SECRET, django_capture_on_commit_callbacks)
    sms.assert_not_called()


def test_without_the_users_consent_nothing_is_sent(guest, staff, sms, django_capture_on_commit_callbacks):
    User.objects.filter(pk=guest.pk).update(sms_notifications=False)
    reply(conversation_after_question(guest, django_capture_on_commit_callbacks), staff, 'hi', django_capture_on_commit_callbacks)
    sms.assert_not_called()


def test_without_a_phone_number_nothing_is_sent(guest, staff, sms, django_capture_on_commit_callbacks):
    User.objects.filter(pk=guest.pk).update(phone_number=None)
    reply(conversation_after_question(guest, django_capture_on_commit_callbacks), staff, 'hi', django_capture_on_commit_callbacks)
    sms.assert_not_called()


def test_with_the_switch_off_nothing_is_sent(guest, staff, sms, settings, django_capture_on_commit_callbacks):
    settings.SMS_ENABLED = False
    reply(conversation_after_question(guest, django_capture_on_commit_callbacks), staff, 'hi', django_capture_on_commit_callbacks)
    sms.assert_not_called()


def test_an_inactive_account_gets_nothing(guest, staff, sms, django_capture_on_commit_callbacks):
    conversation = conversation_after_question(guest, django_capture_on_commit_callbacks)
    User.objects.filter(pk=guest.pk).update(is_active=False)
    reply(conversation, staff, 'hi', django_capture_on_commit_callbacks)
    sms.assert_not_called()


def test_a_failing_provider_does_not_stop_the_mail_and_is_recorded(guest, staff, sms, django_capture_on_commit_callbacks):
    conversation = conversation_after_question(guest, django_capture_on_commit_callbacks)
    mail.outbox.clear()
    sms.side_effect = RuntimeError('provider down')
    reply(conversation, staff, 'hi', django_capture_on_commit_callbacks)
    assert [m.to for m in mail.outbox] == [['guest@example.com']]
    assert SmsDelivery.objects.get(user=guest).status == SmsDelivery.FAILED


def test_a_user_gets_at_most_three_sms_a_day(guest, staff, sms, django_capture_on_commit_callbacks):
    conversation = conversation_after_question(guest, django_capture_on_commit_callbacks)
    for minutes in (30, 60, 120):
        delivered(guest, minutes)
    reply(conversation, staff, 'hi', django_capture_on_commit_callbacks)
    sms.assert_not_called()


def test_two_sms_within_ten_minutes_are_not_sent(guest, staff, sms, django_capture_on_commit_callbacks):
    conversation = conversation_after_question(guest, django_capture_on_commit_callbacks)
    delivered(guest, 5)
    reply(conversation, staff, 'hi', django_capture_on_commit_callbacks)
    sms.assert_not_called()


def test_old_deliveries_and_failed_ones_do_not_count(guest, staff, sms, django_capture_on_commit_callbacks):
    conversation = conversation_after_question(guest, django_capture_on_commit_callbacks)
    for minutes in (25 * 60, 26 * 60, 27 * 60):
        delivered(guest, minutes)
    delivered(guest, 60, status=SmsDelivery.FAILED)
    reply(conversation, staff, 'hi', django_capture_on_commit_callbacks)
    sms.assert_called_once()


def test_the_daily_limit_of_the_whole_site_stops_the_sms_and_tells_the_team_once(
        guest, staff, sms, settings, django_capture_on_commit_callbacks):
    settings.SMS_DAILY_LIMIT = 2
    other = User.objects.create_user(email='other@example.com', password='Pass12345!', phone_number=PHONE)
    delivered(other, 60)
    delivered(other, 120)
    conversation = conversation_after_question(guest, django_capture_on_commit_callbacks)
    with mock.patch('common.tasks.send_telegram_message.delay') as alert, \
            mock.patch('chat.notify.alerts_configured', return_value=True):
        reply(conversation, staff, 'one', django_capture_on_commit_callbacks)
        service.mark_read(conversation, staff=False)
        reply(conversation, staff, 'two', django_capture_on_commit_callbacks)
    sms.assert_not_called()
    assert alert.call_count == 1
