"""Chat with the TICKBRON team: the account's own thread, the team's inbox, unread counts, rules and limits."""
from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from chat import service
from chat.models import Conversation, Message
from permissions.models import Role
from users.models import User

pytestmark = pytest.mark.django_db
CHAT = '/api/v1/chat'
ADMIN = '/api/v1/admin-panel/chat'


def client_for(user=None):
    client = APIClient()
    if user:
        client.force_authenticate(user=user)
    return client


def make_user(email, name='Guest One', owner=False, **extra):
    role = None
    if owner:
        role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
    return User.objects.create_user(email=email, password='Pass12345!', full_name=name, role=role, **extra)


@pytest.fixture
def guest():
    return make_user('guest@example.com', 'Aziz Karimov')


@pytest.fixture
def owner():
    return make_user('owner@example.com', 'Olim Owner', owner=True)


@pytest.fixture
def staff():
    return make_user('staff@example.com', 'Team Member', is_staff=True)


def write(user, text='Hello'):
    return client_for(user).post(f'{CHAT}/messages/', {'text': text}, format='json')


def reply(staff_user, conversation, text='Answer'):
    return client_for(staff_user).post(f'{ADMIN}/conversations/{conversation.pk}/', {'text': text}, format='json')


class TestAccess:
    @pytest.mark.parametrize('method,url', [
        ('get', f'{CHAT}/messages/'), ('post', f'{CHAT}/messages/'), ('post', f'{CHAT}/read/'), ('get', f'{CHAT}/unread/'),
        ('get', f'{ADMIN}/conversations/'), ('get', f'{ADMIN}/unread/'),
    ])
    def test_anonymous_visitors_have_no_access(self, method, url):
        assert getattr(client_for(), method)(url).status_code in (401, 403)

    @pytest.mark.parametrize('method,url', [
        ('get', f'{ADMIN}/conversations/'), ('get', f'{ADMIN}/unread/'),
        ('get', f'{ADMIN}/conversations/1/'), ('post', f'{ADMIN}/conversations/1/'), ('post', f'{ADMIN}/conversations/1/read/'),
    ])
    def test_guests_and_owners_cannot_use_the_team_side(self, method, url, guest, owner):
        assert getattr(client_for(guest), method)(url).status_code == 403
        assert getattr(client_for(owner), method)(url).status_code == 403


class TestWriting:
    def test_the_first_message_creates_the_thread_and_it_is_the_users_only(self, guest):
        response = write(guest, 'I need help with my booking')

        assert response.status_code == 201
        assert (response.json()['text'], response.json()['from_staff']) == ('I need help with my booking', False)
        assert Conversation.objects.filter(user=guest).count() == 1
        write(guest, 'Second')
        assert Conversation.objects.filter(user=guest).count() == 1
        assert Message.objects.filter(conversation__user=guest).count() == 2

    def test_a_hotel_owner_can_write_too(self, owner):
        assert write(owner, 'I want to advertise my hotel').status_code == 201

    @pytest.mark.parametrize('text,code', [('', 'empty'), ('   \n ', 'empty'), ('x' * 2001, 'too_long'), ('<b>hi</b>', 'bad_text')])
    def test_bad_messages_are_refused_with_a_code(self, guest, text, code):
        response = write(guest, text)

        assert response.status_code == 400
        assert response.json()['code'] == code
        assert Message.objects.count() == 0

    def test_a_message_of_exactly_2000_characters_is_fine_and_is_trimmed(self, guest):
        response = write(guest, '  ' + 'x' * 2000 + '  ')

        assert response.status_code == 201
        assert len(response.json()['text']) == 2000

    def test_a_missing_text_is_a_400(self, guest):
        assert client_for(guest).post(f'{CHAT}/messages/', {}, format='json').status_code == 400

    def test_writing_is_limited_to_twenty_messages_a_minute(self, guest):
        cache.clear()
        with patch('chat.throttles.TESTING', False):
            codes = [write(guest, f'm{i}').status_code for i in range(22)]
        cache.clear()

        assert codes[:20] == [201] * 20
        assert codes[20:] == [429, 429]


class TestReading:
    def test_a_user_without_a_thread_gets_an_empty_list(self, guest):
        body = client_for(guest).get(f'{CHAT}/messages/').json()

        assert body == {'messages': [], 'unread': 0}

    def test_the_thread_is_read_oldest_first(self, guest, staff):
        write(guest, 'one')
        conversation = Conversation.objects.get(user=guest)
        reply(staff, conversation, 'two')
        write(guest, 'three')

        texts = [m['text'] for m in client_for(guest).get(f'{CHAT}/messages/').json()['messages']]

        assert texts == ['one', 'two', 'three']

    def test_after_gives_only_newer_messages(self, guest):
        first = write(guest, 'one').json()['id']
        write(guest, 'two')

        body = client_for(guest).get(f'{CHAT}/messages/', {'after': first}).json()

        assert [m['text'] for m in body['messages']] == ['two']
        assert client_for(guest).get(f'{CHAT}/messages/', {'after': 10 ** 9}).json()['messages'] == []

    @pytest.mark.parametrize('value', ['abc', '-1', '1.5'])
    def test_a_bad_after_is_a_400(self, guest, value):
        response = client_for(guest).get(f'{CHAT}/messages/', {'after': value})

        assert response.status_code == 400
        assert response.json()['code'] == 'invalid_query'

    def test_the_first_read_gives_the_last_hundred_oldest_first(self, guest):
        write(guest, 'seed')
        conversation = Conversation.objects.get(user=guest)
        Message.objects.bulk_create([Message(conversation=conversation, sender=guest, text=f'm{i}') for i in range(120)])

        messages = client_for(guest).get(f'{CHAT}/messages/').json()['messages']

        assert len(messages) == service.PAGE == 100
        assert [m['text'] for m in messages][-1] == 'm119'
        assert [m['id'] for m in messages] == sorted(m['id'] for m in messages)

    def test_nobody_sees_the_thread_of_another_account(self, guest, owner, staff):
        write(guest, 'private to the team')
        reply(staff, Conversation.objects.get(user=guest), 'staff answer to the guest')

        assert client_for(owner).get(f'{CHAT}/messages/').json() == {'messages': [], 'unread': 0}


class TestUnreadForTheUser:
    def test_a_reply_of_the_team_is_unread_until_the_user_reads_it(self, guest, staff):
        write(guest, 'help')
        conversation = Conversation.objects.get(user=guest)
        assert client_for(guest).get(f'{CHAT}/unread/').json() == {'unread': 0}

        reply(staff, conversation, 'one')
        reply(staff, conversation, 'two')

        assert client_for(guest).get(f'{CHAT}/unread/').json() == {'unread': 2}
        assert client_for(guest).get(f'{CHAT}/messages/').json()['unread'] == 2
        assert client_for(guest).post(f'{CHAT}/read/').status_code == 204
        assert client_for(guest).get(f'{CHAT}/unread/').json() == {'unread': 0}

    def test_writing_does_not_make_the_users_own_message_unread(self, guest):
        write(guest, 'hello')

        assert service.unread_for_user(guest) == 0

    def test_reading_without_a_thread_is_fine(self, guest):
        assert client_for(guest).post(f'{CHAT}/read/').status_code == 204

    def test_the_read_mark_never_moves_back(self, guest, staff):
        write(guest, 'help')
        conversation = Conversation.objects.get(user=guest)
        reply(staff, conversation)
        service.mark_read(conversation, staff=False)
        conversation.refresh_from_db()
        newest = conversation.user_read_id

        Conversation.objects.filter(pk=conversation.pk).update(user_read_id=newest)
        service.mark_read(conversation, staff=False)

        conversation.refresh_from_db()
        assert conversation.user_read_id == newest


class TestTheInbox:
    def test_threads_come_newest_activity_first_with_unread_counts_and_who_wrote(self, guest, owner, staff):
        write(guest, 'first thread')
        write(owner, 'I want to advertise')
        write(owner, 'second message')
        write(guest, 'guest again')

        rows = client_for(staff).get(f'{ADMIN}/conversations/').json()['results']

        assert [row['user']['email'] for row in rows] == ['guest@example.com', 'owner@example.com']
        assert [row['unread'] for row in rows] == [2, 2]
        assert rows[0]['user'] == {'id': guest.pk, 'name': 'Aziz Karimov', 'email': 'guest@example.com', 'role': 'customer'}
        assert rows[1]['user']['role'] == 'hotel-owner'
        assert rows[0]['last_message']['text'] == 'guest again'
        assert rows[0]['last_message']['from_staff'] is False

    def test_the_preview_is_cut_at_120_characters(self, guest, staff):
        write(guest, 'y' * 500)

        row = client_for(staff).get(f'{ADMIN}/conversations/').json()['results'][0]

        assert len(row['last_message']['text']) == 120

    def test_only_unread_threads_can_be_asked_for(self, guest, owner, staff):
        write(guest, 'a')
        write(owner, 'b')
        service.mark_read(Conversation.objects.get(user=owner), staff=True)

        rows = client_for(staff).get(f'{ADMIN}/conversations/', {'unread': 'true'}).json()['results']

        assert [row['user']['email'] for row in rows] == ['guest@example.com']

    @pytest.mark.parametrize('term', ['aziz', 'KARIMOV', 'guest@example'])
    def test_search_finds_a_thread_by_name_or_email(self, guest, owner, staff, term):
        write(guest, 'a')
        write(owner, 'b')

        rows = client_for(staff).get(f'{ADMIN}/conversations/', {'q': term}).json()['results']

        assert [row['user']['email'] for row in rows] == ['guest@example.com']

    def test_staff_and_super_admin_both_see_the_inbox(self, guest, staff):
        write(guest, 'a')
        root = User.objects.create_superuser(email='root@example.com', password='Pass12345!')

        assert client_for(staff).get(f'{ADMIN}/conversations/').json()['count'] == 1
        assert client_for(root).get(f'{ADMIN}/conversations/').json()['count'] == 1


class TestTheTeamsThread:
    def test_the_team_reads_a_thread_with_the_user(self, guest, staff):
        write(guest, 'one')
        conversation = Conversation.objects.get(user=guest)

        body = client_for(staff).get(f'{ADMIN}/conversations/{conversation.pk}/').json()

        assert [m['text'] for m in body['messages']] == ['one']
        assert body['user']['email'] == 'guest@example.com'

    def test_after_works_for_the_team_too(self, guest, staff):
        first = write(guest, 'one').json()['id']
        write(guest, 'two')
        conversation = Conversation.objects.get(user=guest)

        body = client_for(staff).get(f'{ADMIN}/conversations/{conversation.pk}/', {'after': first}).json()

        assert [m['text'] for m in body['messages']] == ['two']
        assert client_for(staff).get(f'{ADMIN}/conversations/{conversation.pk}/', {'after': 'x'}).status_code == 400

    def test_an_unknown_thread_is_404(self, staff):
        assert client_for(staff).get(f'{ADMIN}/conversations/999/').status_code == 404
        assert client_for(staff).post(f'{ADMIN}/conversations/999/', {'text': 'hi'}, format='json').status_code == 404
        assert client_for(staff).post(f'{ADMIN}/conversations/999/read/').status_code == 404

    def test_a_reply_is_from_the_team_reaches_the_user_and_clears_the_teams_unread(self, guest, staff):
        write(guest, 'help')
        conversation = Conversation.objects.get(user=guest)

        response = reply(staff, conversation, 'We are on it')

        assert response.status_code == 201
        assert response.json()['from_staff'] is True
        assert client_for(guest).get(f'{CHAT}/messages/').json()['unread'] == 1
        row = client_for(staff).get(f'{ADMIN}/conversations/').json()['results'][0]
        assert row['unread'] == 0
        assert Message.objects.filter(conversation=conversation).order_by('-id').first().sender_id == staff.pk

    def test_replies_follow_the_same_text_rules(self, guest, staff):
        write(guest, 'help')
        conversation = Conversation.objects.get(user=guest)

        assert reply(staff, conversation, '  ').json()['code'] == 'empty'
        assert reply(staff, conversation, 'z' * 2001).json()['code'] == 'too_long'
        assert reply(staff, conversation, '<a>').json()['code'] == 'bad_text'

    def test_the_badge_counts_threads_with_messages_the_team_has_not_read(self, guest, owner, staff):
        write(guest, 'a')
        write(owner, 'b')
        write(owner, 'c')
        assert client_for(staff).get(f'{ADMIN}/unread/').json() == {'unread_threads': 2}

        assert client_for(staff).post(f'{ADMIN}/conversations/{Conversation.objects.get(user=owner).pk}/read/').status_code == 204

        assert client_for(staff).get(f'{ADMIN}/unread/').json() == {'unread_threads': 1}
        write(owner, 'd')
        assert client_for(staff).get(f'{ADMIN}/unread/').json() == {'unread_threads': 2}
