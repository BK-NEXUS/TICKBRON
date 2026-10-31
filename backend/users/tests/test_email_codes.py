"""
A six-digit code mailed to the address: at sign-up (the account is made only after the code is typed) and at every
sign-in of a guest or hotel owner (after the password, before the session). Plan: .ai/PLAN_EMAIL_CODES.md.
"""
import re
from unittest import mock

import pytest
from django.core import mail
from django.core.cache import cache
from rest_framework.test import APIClient

from users import email_codes
from users.models import User

pytestmark = pytest.mark.django_db

REGISTER = '/api/v1/auth/register/'
VERIFY = '/api/v1/auth/register/verify/'
RESEND = '/api/v1/auth/register/resend/'
LOGIN = '/api/v1/auth/login/'
LOGIN_CODE = '/api/v1/auth/login/email-code/'
LOGIN_RESEND = '/api/v1/auth/login/email-code/resend/'
ME = '/api/v1/auth/me/'
PASSWORD = 'Kitob7$yy'
NOW = 2_000_000_000.0


@pytest.fixture(autouse=True)
def codes_on(settings):
    settings.EMAIL_VERIFICATION_REQUIRED = True
    settings.EMAIL_LOGIN_CODE_REQUIRED = True


@pytest.fixture
def clock():
    """The moment the code module sees; tests move it with clock.now."""
    class Clock:
        now = NOW
    with mock.patch.object(email_codes, '_now', side_effect=lambda: Clock.now):
        yield Clock


def sign_up_body(**extra):
    return {'email': 'new.guest@example.com', 'full_name': 'New Guest', 'phone_number': '+998901234567',
            'password': PASSWORD, 'password_confirm': PASSWORD, **extra}


def code_in_last_mail():
    found = re.search(r'\b(\d{6})\b', mail.outbox[-1].body)
    assert found, mail.outbox[-1].body
    return found.group(1)


def wrong_code(real):
    return '000000' if real != '000000' else '111111'


def start_sign_up(api=None, **extra):
    api = api or APIClient()
    response = api.post(REGISTER, sign_up_body(**extra), format='json')
    return api, response


class TestSignUp:
    def test_the_account_is_not_made_until_the_code_is_typed(self):
        _, response = start_sign_up()

        assert response.status_code == 202, response.data
        assert response.data['email_code_required'] is True and response.data['email'] == 'new.guest@example.com'
        assert not User.objects.filter(email='new.guest@example.com').exists()
        assert len(mail.outbox) == 1 and mail.outbox[0].to == ['new.guest@example.com']

    def test_the_answer_never_holds_the_code_or_the_password(self):
        _, response = start_sign_up()

        assert code_in_last_mail() not in str(response.data) and PASSWORD not in str(response.data)

    def test_the_right_code_makes_the_account_and_signs_it_in(self):
        api, _ = start_sign_up()

        response = api.post(VERIFY, {'email': 'new.guest@example.com', 'code': code_in_last_mail()}, format='json')

        assert response.status_code == 201, response.data
        user = User.objects.get(email='new.guest@example.com')
        assert user.email_verified is True and user.check_password(PASSWORD)
        assert user.full_name == 'New Guest' and user.phone_number == '+998901234567'
        assert api.get(ME).status_code == 200

    def test_the_address_is_lowercased_and_trimmed(self):
        api, _ = start_sign_up(email='  New.Guest@Example.COM ')

        response = api.post(VERIFY, {'email': 'NEW.guest@example.com ', 'code': code_in_last_mail()}, format='json')

        assert response.status_code == 201 and User.objects.filter(email='new.guest@example.com').exists()

    def test_a_wrong_code_is_refused_and_makes_no_account(self):
        api, _ = start_sign_up()

        response = api.post(VERIFY, {'email': 'new.guest@example.com', 'code': wrong_code(code_in_last_mail())}, format='json')

        assert response.status_code == 400
        assert not User.objects.filter(email='new.guest@example.com').exists()

    def test_five_wrong_codes_burn_the_code_even_for_the_right_one(self):
        api, _ = start_sign_up()
        real = code_in_last_mail()
        for _ in range(email_codes.MAX_ATTEMPTS):
            api.post(VERIFY, {'email': 'new.guest@example.com', 'code': wrong_code(real)}, format='json')

        response = api.post(VERIFY, {'email': 'new.guest@example.com', 'code': real}, format='json')

        assert response.status_code == 400 and not User.objects.filter(email='new.guest@example.com').exists()

    def test_a_code_works_once(self):
        api, _ = start_sign_up()
        real = code_in_last_mail()
        api.post(VERIFY, {'email': 'new.guest@example.com', 'code': real}, format='json')

        again = APIClient().post(VERIFY, {'email': 'new.guest@example.com', 'code': real}, format='json')

        assert again.status_code == 400

    def test_a_code_stops_working_after_ten_minutes(self, clock):
        api, _ = start_sign_up()
        real = code_in_last_mail()
        clock.now += email_codes.LIFETIME_SECONDS + 1

        response = api.post(VERIFY, {'email': 'new.guest@example.com', 'code': real}, format='json')

        assert response.status_code == 400 and not User.objects.filter(email='new.guest@example.com').exists()

    def test_the_code_belongs_to_the_address_it_was_sent_to(self):
        api, _ = start_sign_up()
        real = code_in_last_mail()

        response = api.post(VERIFY, {'email': 'someone.else@example.com', 'code': real}, format='json')

        assert response.status_code == 400

    @pytest.mark.parametrize('body', [
        {}, {'email': 'new.guest@example.com'}, {'code': '123456'}, {'email': 'new.guest@example.com', 'code': ['1']},
        {'email': ['x'], 'code': '123456'}, {'email': 'new.guest@example.com', 'code': None}, ['x'], 'text',
        {'email': 'new.guest@example.com', 'code': '12'}, {'email': 'new.guest@example.com', 'code': 'abcdef'},
        {'email': 'new.guest@example.com', 'code': '1' * 500}, {'email': 'new.guest@example.com', 'code': '12345\x00'},
    ])
    def test_a_bad_request_is_a_400_never_a_500(self, body):
        start_sign_up()

        assert APIClient().post(VERIFY, body, format='json').status_code == 400

    def test_nothing_is_mailed_for_a_sign_up_that_is_not_valid(self):
        for change in ({'email': 'not-an-email'}, {'password_confirm': 'different'}, {'phone_number': 'abc'}):
            _, response = start_sign_up(**change)
            assert response.status_code == 400
        assert mail.outbox == []

    def test_an_address_that_already_has_an_account_is_refused_before_any_mail(self):
        User.objects.create_user(email='new.guest@example.com', password=PASSWORD)

        _, response = start_sign_up()

        assert response.status_code == 400 and 'email' in response.data and mail.outbox == []

    def test_an_account_made_meanwhile_does_not_cause_a_500(self):
        api, _ = start_sign_up()
        real = code_in_last_mail()
        User.objects.create_user(email='new.guest@example.com', password='Other#Pass9')

        response = api.post(VERIFY, {'email': 'new.guest@example.com', 'code': real}, format='json')

        assert response.status_code == 400 and User.objects.filter(email='new.guest@example.com').count() == 1

    def test_the_waiting_data_holds_neither_the_code_nor_the_password_as_text(self):
        start_sign_up()
        real = code_in_last_mail()

        stored = repr(cache.get(email_codes.entry_key('register', 'new.guest@example.com')))

        assert stored != 'None' and real not in stored and PASSWORD not in stored

    def test_a_mail_server_that_fails_gives_a_503_and_leaves_nothing_waiting(self):
        with mock.patch('users.email_codes.send_mail', side_effect=OSError('smtp down')):
            _, response = start_sign_up()

        assert response.status_code == 503
        assert not User.objects.filter(email='new.guest@example.com').exists()
        _, again = start_sign_up()
        assert again.status_code == 202  # no cool-down for a mail that never left

    def test_the_mail_says_who_sent_it_and_to_ignore_it_if_unasked(self):
        start_sign_up()
        body = mail.outbox[0].body

        assert 'TICKBRON' in mail.outbox[0].subject and 'TICKBRON' in body
        assert code_in_last_mail() in body
        for language_marker in ('Uz:', 'Ru:', 'En:'):
            assert language_marker in body


class TestSignUpResend:
    def test_a_new_code_cannot_be_asked_for_at_once(self, clock):
        api, _ = start_sign_up()

        assert api.post(RESEND, {'email': 'new.guest@example.com'}, format='json').status_code == 429
        assert len(mail.outbox) == 1

    def test_after_the_wait_a_new_code_comes_and_the_old_one_dies(self, clock):
        api, _ = start_sign_up()
        old = code_in_last_mail()
        clock.now += email_codes.RESEND_AFTER_SECONDS + 1

        response = api.post(RESEND, {'email': 'new.guest@example.com'}, format='json')
        new = code_in_last_mail()

        assert response.status_code == 200 and len(mail.outbox) == 2
        if new != old:
            assert api.post(VERIFY, {'email': 'new.guest@example.com', 'code': old}, format='json').status_code == 400
        assert api.post(VERIFY, {'email': 'new.guest@example.com', 'code': new}, format='json').status_code == 201

    def test_at_most_five_mails_an_hour_to_one_address(self, clock):
        api, _ = start_sign_up()
        sent = 1
        for _ in range(10):
            clock.now += email_codes.RESEND_AFTER_SECONDS + 1
            if api.post(RESEND, {'email': 'new.guest@example.com'}, format='json').status_code == 200:
                sent += 1

        assert sent == email_codes.MAX_SENDS_PER_HOUR

    def test_there_is_nothing_to_resend_without_a_started_sign_up(self):
        assert APIClient().post(RESEND, {'email': 'nobody@example.com'}, format='json').status_code == 400
        assert mail.outbox == []

    @pytest.mark.parametrize('body', [{}, {'email': ['x']}, ['x'], 'text', {'email': None}])
    def test_a_bad_resend_is_a_400(self, body):
        assert APIClient().post(RESEND, body, format='json').status_code == 400


class TestFlagsOff:
    def test_sign_up_is_as_before_when_the_switch_is_off(self, settings):
        settings.EMAIL_VERIFICATION_REQUIRED = False

        _, response = start_sign_up()

        assert response.status_code == 201 and mail.outbox == []
        assert User.objects.filter(email='new.guest@example.com').exists()

    def test_sign_in_is_as_before_when_the_switch_is_off(self, settings):
        settings.EMAIL_LOGIN_CODE_REQUIRED = False
        User.objects.create_user(email='g@example.com', password=PASSWORD)

        response = APIClient().post(LOGIN, {'email': 'g@example.com', 'password': PASSWORD}, format='json')

        assert response.status_code == 200 and mail.outbox == []


def guest(email='guest@example.com', **extra):
    return User.objects.create_user(email=email, password=PASSWORD, **extra)


def password_step(email='guest@example.com'):
    api = APIClient()
    return api, api.post(LOGIN, {'email': email, 'password': PASSWORD}, format='json')


class TestSignIn:
    def test_the_right_password_mails_a_code_and_signs_nobody_in_yet(self):
        guest()

        api, response = password_step()

        assert response.status_code == 200 and response.data['email_code_required'] is True
        assert response.data['email_hint'] == 'g***@example.com'
        assert len(mail.outbox) == 1 and mail.outbox[0].to == ['guest@example.com']
        assert api.get(ME).status_code in (401, 403)

    def test_the_right_code_signs_in_and_confirms_the_address(self):
        guest()
        api, _ = password_step()

        response = api.post(LOGIN_CODE, {'code': code_in_last_mail()}, format='json')

        assert response.status_code == 200 and response.data['email'] == 'guest@example.com'
        assert api.get(ME).status_code == 200
        assert User.objects.get(email='guest@example.com').email_verified is True

    def test_a_wrong_password_mails_nothing(self):
        guest()

        response = APIClient().post(LOGIN, {'email': 'guest@example.com', 'password': 'Wrong#Pass1'}, format='json')

        assert response.status_code == 401 and mail.outbox == []

    def test_an_unknown_address_mails_nothing(self):
        response = APIClient().post(LOGIN, {'email': 'nobody@example.com', 'password': PASSWORD}, format='json')

        assert response.status_code == 401 and mail.outbox == []

    def test_a_wrong_code_is_the_same_401_as_a_wrong_password_and_signs_nobody_in(self):
        guest()
        api, _ = password_step()

        response = api.post(LOGIN_CODE, {'code': wrong_code(code_in_last_mail())}, format='json')

        assert response.status_code == 401
        assert api.get(ME).status_code in (401, 403)

    def test_five_wrong_codes_burn_the_code(self):
        guest()
        api, _ = password_step()
        real = code_in_last_mail()
        for _ in range(email_codes.MAX_ATTEMPTS):
            api.post(LOGIN_CODE, {'code': wrong_code(real)}, format='json')

        assert api.post(LOGIN_CODE, {'code': real}, format='json').status_code == 401

    def test_wrong_codes_count_towards_the_account_lock_like_wrong_passwords(self):
        from users import lockout
        user = guest()
        api, _ = password_step()
        real = code_in_last_mail()
        for _ in range(lockout.IP_FAILURE_LIMIT):
            api.post(LOGIN_CODE, {'code': wrong_code(real)}, format='json')

        assert lockout.is_locked(user, '127.0.0.1')

    def test_there_is_no_code_step_without_the_password_step(self):
        guest()

        assert APIClient().post(LOGIN_CODE, {'code': '123456'}, format='json').status_code == 401

    def test_the_password_step_is_forgotten_after_five_minutes(self, clock):
        guest()
        api, _ = password_step()
        real = code_in_last_mail()
        clock.now += email_codes.LIFETIME_SECONDS + 1

        assert api.post(LOGIN_CODE, {'code': real}, format='json').status_code == 401

    def test_a_code_of_one_account_does_not_open_another_session(self):
        guest('first@example.com')
        guest('second@example.com')
        api_first, _ = password_step('first@example.com')
        first_code = code_in_last_mail()
        api_second, _ = password_step('second@example.com')

        response = api_second.post(LOGIN_CODE, {'code': first_code}, format='json')

        assert response.status_code == 401
        assert api_first.post(LOGIN_CODE, {'code': first_code}, format='json').status_code == 200

    def test_a_code_works_once(self):
        guest()
        api, _ = password_step()
        real = code_in_last_mail()
        api.post(LOGIN_CODE, {'code': real}, format='json')
        api.post('/api/v1/auth/logout/', {}, format='json')

        assert api.post(LOGIN_CODE, {'code': real}, format='json').status_code == 401

    @pytest.mark.parametrize('body', [{}, {'code': ['1']}, {'code': None}, ['x'], 'text', {'code': '12'}, {'code': 'abcdef'},
                                       {'code': '1' * 500}, {'code': '12345\x00'}])
    def test_a_bad_request_is_a_401_or_400_never_a_500(self, body):
        guest()
        api, _ = password_step()

        assert api.post(LOGIN_CODE, body, format='json').status_code in (400, 401)

    def test_a_hotel_owner_gets_the_code_too(self):
        from permissions.models import Role
        role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
        guest('owner@example.com', role=role)

        _, response = password_step('owner@example.com')

        assert response.data['email_code_required'] is True

    def test_staff_with_the_authenticator_use_it_and_get_no_mail(self):
        from users import two_factor
        staff = guest('staff@example.com', is_staff=True)
        two_factor.enable(staff, two_factor.new_secret(), step=0)

        _, response = password_step('staff@example.com')

        assert response.data == {'two_factor_required': True} and mail.outbox == []

    def test_staff_without_the_authenticator_are_not_asked_for_a_mailed_code(self):
        guest('staff@example.com', is_staff=True)

        _, response = password_step('staff@example.com')

        assert response.status_code == 200 and 'email_code_required' not in response.data and mail.outbox == []

    def test_an_inactive_account_gets_nothing(self):
        guest(is_active=False)

        _, response = password_step()

        assert response.status_code == 401 and mail.outbox == []

    def test_a_mail_server_that_fails_gives_a_503_and_no_session(self):
        guest()
        with mock.patch('users.email_codes.send_mail', side_effect=OSError('smtp down')):
            api, response = password_step()

        assert response.status_code == 503 and api.get(ME).status_code in (401, 403)


class TestSignInResend:
    def test_a_new_code_needs_a_wait_and_the_password_step(self, clock):
        guest()
        api, _ = password_step()
        assert api.post(LOGIN_RESEND, {}, format='json').status_code == 429
        clock.now += email_codes.RESEND_AFTER_SECONDS + 1

        response = api.post(LOGIN_RESEND, {}, format='json')

        assert response.status_code == 200 and len(mail.outbox) == 2
        assert api.post(LOGIN_CODE, {'code': code_in_last_mail()}, format='json').status_code == 200

    def test_without_the_password_step_there_is_nothing_to_resend(self):
        assert APIClient().post(LOGIN_RESEND, {}, format='json').status_code == 401
        assert mail.outbox == []


class TestCodeModule:
    def test_a_code_is_six_digits(self):
        for _ in range(200):
            assert re.fullmatch(r'\d{6}', email_codes.new_code())

    def test_the_hint_hides_most_of_the_address(self):
        assert email_codes.hint('olim.karimov@gmail.com') == 'o***@gmail.com'
        assert email_codes.hint('a@b.co') == 'a***@b.co'
