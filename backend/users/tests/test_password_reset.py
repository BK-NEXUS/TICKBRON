"""
OWASP A07-1: a forgotten password can be reset by e-mail, and a known password can be changed.

The reset link is a signed, single-use token (valid for PASSWORD_RESET_TIMEOUT). The request
endpoint answers the same for every address, so it cannot be used to find out who has an account.
"""
import logging
import re
from unittest import mock

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from accounts.models import AccountHistory
from users.models import User
from users.tasks import send_password_reset_email

OLD_PASSWORD = 'Old-Password#2026'
NEW_PASSWORD = 'Fresh9Grape#Tower42'
EMAIL = 'forgetful@example.com'

REQUEST_URL = '/api/v1/auth/password-reset/request/'
CONFIRM_URL = '/api/v1/auth/password-reset/confirm/'
CHANGE_URL = '/api/v1/auth/password/change/'
LINK_PATTERN = re.compile(r'/reset-password\?uid=([\w-]+)&token=([\w-]+)')


@pytest.fixture(autouse=True)
def _clean_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def send_mail_immediately():
    """The Celery task runs inline, so a test sees the mail the worker would send."""
    with mock.patch('users.tasks.send_password_reset_email.delay',
                    side_effect=lambda user_id: send_password_reset_email.run(user_id)):
        yield


@pytest.fixture
def user(db):
    return User.objects.create_user(email=EMAIL, password=OLD_PASSWORD, full_name='Forgetful Guest')


@pytest.fixture
def security(caplog):
    caplog.set_level(logging.INFO, logger='tickbron.security')
    return caplog


def browser():
    """A client that enforces CSRF like a real browser."""
    client = APIClient(enforce_csrf_checks=True)
    return client, client.get('/api/v1/auth/csrf/').data['csrf_token']


def reset_link_from(mailbox):
    """(uid, token) from the only mail in the outbox."""
    [message] = mailbox
    return LINK_PATTERN.search(message.body).groups()


def request_reset(email=EMAIL):
    return APIClient().post(REQUEST_URL, {'email': email}, format='json')


def confirm(uid, token, password=NEW_PASSWORD, confirmation=None):
    return APIClient().post(CONFIRM_URL, {
        'uid': uid, 'token': token, 'password': password,
        'password_confirm': password if confirmation is None else confirmation,
    }, format='json')


def login(password, email=EMAIL):
    return APIClient().post('/api/v1/auth/login/', {'email': email, 'password': password}, format='json')


@pytest.mark.django_db
class TestRequestingAReset:
    def test_a_registered_address_gets_one_mail_with_a_working_link(self, user, mailoutbox, settings):
        settings.FRONTEND_URL = 'https://tickbron.example'

        assert request_reset().status_code == 200

        [message] = mailoutbox
        assert message.to == [EMAIL]
        assert 'https://tickbron.example/reset-password?uid=' in message.body
        uid, token = reset_link_from(mailoutbox)
        assert confirm(uid, token).status_code == 200

    def test_the_answer_is_the_same_for_a_registered_and_an_unknown_address(self, user, mailoutbox):
        known = request_reset(EMAIL)
        unknown = request_reset('nobody@example.com')

        assert (known.status_code, known.data) == (unknown.status_code, unknown.data)
        assert len(mailoutbox) == 1

    def test_a_deactivated_account_gets_no_mail(self, user, mailoutbox):
        User.objects.filter(pk=user.pk).update(is_active=False)

        assert request_reset().status_code == 200
        assert mailoutbox == []

    def test_an_account_without_a_password_gets_no_mail(self, db, mailoutbox):
        phone_only = User.objects.create_user(email='phone-only@example.com', password=None)

        assert request_reset(phone_only.email).status_code == 200
        assert mailoutbox == []

    def test_one_address_gets_at_most_five_mails_a_day(self, user, mailoutbox):
        answers = [request_reset().status_code for _ in range(7)]

        assert answers == [200] * 7
        assert len(mailoutbox) == 5

    def test_a_token_is_required_like_for_login(self, user, mailoutbox):
        client, _ = browser()

        response = client.post(REQUEST_URL, {'email': EMAIL}, format='json')

        assert response.status_code == 403
        assert mailoutbox == []

    def test_the_ip_is_limited(self, user):
        from users import throttles
        with mock.patch('users.throttles.TESTING', False), \
                mock.patch.object(throttles.PasswordResetRequestThrottle, 'rate', '2/hour'):
            codes = [request_reset(f'user{n}@example.com').status_code for n in range(3)]

        assert codes == [200, 200, 429]

    def test_the_event_names_the_account_but_not_the_address(self, user, security):
        request_reset()

        [line] = [r.getMessage() for r in security.records if 'password_reset_requested' in r.getMessage()]
        assert f'user={user.id}' in line
        assert EMAIL not in line


@pytest.mark.django_db
class TestConfirmingAReset:
    def reset_link(self, mailoutbox):
        request_reset()
        return reset_link_from(mailoutbox)

    def test_the_new_password_works_and_the_old_one_does_not(self, user, mailoutbox):
        uid, token = self.reset_link(mailoutbox)

        assert confirm(uid, token).status_code == 200

        assert login(NEW_PASSWORD).status_code == 200
        assert login(OLD_PASSWORD).status_code == 401

    def test_the_link_works_once(self, user, mailoutbox):
        uid, token = self.reset_link(mailoutbox)
        confirm(uid, token)

        again = confirm(uid, token, password='Quiet7Lemon#River58')

        assert again.status_code == 400
        assert login(NEW_PASSWORD).status_code == 200

    def test_an_expired_link_is_refused(self, user, mailoutbox, settings):
        uid, token = self.reset_link(mailoutbox)
        settings.PASSWORD_RESET_TIMEOUT = -1

        assert confirm(uid, token).status_code == 400
        assert login(OLD_PASSWORD).status_code == 200

    @pytest.mark.parametrize('uid, token', [('not-an-id', 'x'), ('MQ', 'wrong-token')])
    def test_a_broken_link_gets_the_one_generic_answer(self, user, uid, token):
        response = confirm(uid, token)

        assert response.status_code == 400
        assert response.data == {'error': 'This link is invalid or has expired. Please request a new one.',
                                 'code': 'invalid_reset_link'}

    def test_a_valid_token_of_a_deactivated_account_is_refused(self, user, mailoutbox):
        uid, token = self.reset_link(mailoutbox)
        User.objects.filter(pk=user.pk).update(is_active=False)

        assert confirm(uid, token).status_code == 400

    def test_a_weak_password_is_refused_and_the_link_stays_usable(self, user, mailoutbox):
        uid, token = self.reset_link(mailoutbox)

        weak = confirm(uid, token, password='12345678')

        assert weak.status_code == 400
        assert 'password' in weak.data
        assert confirm(uid, token).status_code == 200

    def test_a_mismatching_confirmation_is_refused(self, user, mailoutbox):
        uid, token = self.reset_link(mailoutbox)

        assert confirm(uid, token, confirmation='something else').status_code == 400
        assert login(OLD_PASSWORD).status_code == 200

    def test_a_locked_account_can_sign_in_again_after_a_reset(self, user, mailoutbox):
        for _ in range(6):
            login('wrong-password-123')
        assert login(OLD_PASSWORD).status_code == 401  # locked out of this account from this address
        uid, token = self.reset_link(mailoutbox)

        confirm(uid, token)

        assert login(NEW_PASSWORD).status_code == 200

    def test_other_sessions_end(self, user, mailoutbox):
        other_device = APIClient()
        other_device.post('/api/v1/auth/login/', {'email': EMAIL, 'password': OLD_PASSWORD}, format='json')
        assert other_device.get('/api/v1/auth/me/').status_code == 200
        uid, token = self.reset_link(mailoutbox)

        confirm(uid, token)

        assert other_device.get('/api/v1/auth/me/').status_code in (401, 403)

    def test_it_does_not_sign_the_user_in(self, user, mailoutbox):
        uid, token = self.reset_link(mailoutbox)
        client = APIClient()

        client.post(CONFIRM_URL, {'uid': uid, 'token': token, 'password': NEW_PASSWORD,
                                  'password_confirm': NEW_PASSWORD}, format='json')

        assert client.get('/api/v1/auth/me/').status_code in (401, 403)

    def test_history_and_event_are_written_without_secrets(self, user, mailoutbox, security):
        uid, token = self.reset_link(mailoutbox)

        confirm(uid, token)

        assert AccountHistory.objects.filter(user=user, action='password_change').exists()
        text = ' '.join(r.getMessage() for r in security.records)
        assert 'password_reset_completed' in text
        assert token not in text and NEW_PASSWORD not in text and EMAIL not in text

    def test_a_token_is_required_like_for_login(self, user, mailoutbox):
        uid, token = self.reset_link(mailoutbox)
        client, _ = browser()

        response = client.post(CONFIRM_URL, {'uid': uid, 'token': token, 'password': NEW_PASSWORD,
                                             'password_confirm': NEW_PASSWORD}, format='json')

        assert response.status_code == 403
        assert login(OLD_PASSWORD).status_code == 200


@pytest.mark.django_db
class TestChangingThePassword:
    @pytest.fixture
    def session(self, user):
        client = APIClient()
        client.post('/api/v1/auth/login/', {'email': EMAIL, 'password': OLD_PASSWORD}, format='json')
        return client

    def change(self, client, current=OLD_PASSWORD, new=NEW_PASSWORD, confirmation=None):
        return client.post(CHANGE_URL, {
            'current_password': current, 'password': new,
            'password_confirm': new if confirmation is None else confirmation,
        }, format='json')

    def test_it_changes_the_password_and_keeps_this_session(self, session):
        assert self.change(session).status_code == 200

        assert session.get('/api/v1/auth/me/').status_code == 200
        assert login(NEW_PASSWORD).status_code == 200
        assert login(OLD_PASSWORD).status_code == 401

    def test_other_sessions_end(self, session):
        other_device = APIClient()
        other_device.post('/api/v1/auth/login/', {'email': EMAIL, 'password': OLD_PASSWORD}, format='json')

        self.change(session)

        assert other_device.get('/api/v1/auth/me/').status_code in (401, 403)

    def test_a_wrong_current_password_is_refused_and_counted_as_a_failed_attempt(self, session, user):
        response = self.change(session, current='not-my-password-123')

        assert response.status_code == 400
        assert 'current_password' in response.data
        user.refresh_from_db()
        assert user.failed_login_attempts == 1
        assert login(OLD_PASSWORD).status_code == 200

    @pytest.mark.parametrize('new, confirmation', [('12345678', None), (NEW_PASSWORD, 'something else'),
                                                   (OLD_PASSWORD, None)])
    def test_a_weak_mismatching_or_unchanged_password_is_refused(self, session, new, confirmation):
        assert self.change(session, new=new, confirmation=confirmation).status_code == 400
        assert login(OLD_PASSWORD).status_code == 200

    def test_it_needs_a_session(self, user):
        assert self.change(APIClient()).status_code in (401, 403)

    def test_history_and_event_are_written_without_secrets(self, session, user, security):
        self.change(session)

        assert AccountHistory.objects.filter(user=user, action='password_change').exists()
        text = ' '.join(r.getMessage() for r in security.records)
        assert 'password_changed' in text
        assert NEW_PASSWORD not in text and OLD_PASSWORD not in text

    def test_the_account_is_limited_to_five_attempts_a_minute(self, session):
        from users import throttles
        with mock.patch('users.throttles.TESTING', False):
            codes = [self.change(session, current='not-my-password-123').status_code for _ in range(6)]

        assert codes[-1] == 429
        assert throttles.PasswordChangeThrottle.rate == '5/min'
