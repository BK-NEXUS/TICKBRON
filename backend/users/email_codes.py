"""
Six-digit codes mailed to an address, to show that the person at the keyboard has the mailbox: at sign-up (the account
is made only after the code is typed) and at every sign-in of a guest or a hotel owner (after the password, before the
session starts). Plan: .ai/PLAN_EMAIL_CODES.md.

- The code is random (`secrets`), lives 10 minutes, works once, and is kept only as a keyed hash in the cache.
- 5 wrong tries burn it. A new code can be asked for after a minute, at most 5 mails an hour to one address.
- A waiting sign-up keeps the typed data, the password already hashed, in the cache for those 10 minutes.
- The mail is sent inside the request, not through the task queue, so the code never passes through the queue's logs.
"""
import hashlib
import hmac
import secrets
import time

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import salted_hmac

CODE_LENGTH = 6
LIFETIME_SECONDS = 10 * 60
MAX_ATTEMPTS = 5
RESEND_AFTER_SECONDS = 60
MAX_SENDS_PER_HOUR = 5
HOUR_SECONDS = 60 * 60
EMAIL_SUBJECT = 'TICKBRON: tasdiqlash kodi / код подтверждения / verification code'
LOGIN_PENDING_KEY = 'email_code_login'


class SendFailed(Exception):
    """The mail server did not take the mail."""


class TooSoon(Exception):
    """A new code was asked for too early or too often; `retry_after` is in seconds."""

    def __init__(self, retry_after):
        super().__init__(retry_after)
        self.retry_after = retry_after


def _now():
    return time.time()


def new_code():
    return f'{secrets.randbelow(10 ** CODE_LENGTH):0{CODE_LENGTH}d}'


def looks_like_a_code(value):
    return isinstance(value, str) and len(value) == CODE_LENGTH and value.isascii() and value.isdigit()


def hint(email):
    """"o***@gmail.com": enough for a person to recognise their own address."""
    name, _, domain = email.partition('@')
    return f'{name[:1]}***@{domain}'


def _fingerprint(*parts):
    return hashlib.sha256(':'.join(parts).encode('utf-8', 'surrogatepass')).hexdigest()


def entry_key(purpose, ident):
    return f'email_code:{purpose}:{_fingerprint(purpose, ident)}'


def _tries_key(purpose, ident):
    return f'email_code_tries:{purpose}:{_fingerprint(purpose, ident)}'


def _sends_key(purpose, ident):
    return f'email_code_sends:{purpose}:{_fingerprint(purpose, ident)}'


def _digest(purpose, ident, code):
    return salted_hmac('tickbron.email_code', f'{purpose}:{ident}:{code}', algorithm='sha256').hexdigest()


def _count_send(purpose, ident):
    key = _sends_key(purpose, ident)
    cache.add(key, 0, HOUR_SECONDS)
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, HOUR_SECONDS)
        return 1


def _check_may_send(purpose, ident):
    entry = cache.get(entry_key(purpose, ident))
    if entry is not None:
        wait = entry['sent_at'] + RESEND_AFTER_SECONDS - _now()
        if wait > 0:
            raise TooSoon(int(wait) + 1)
    if (cache.get(_sends_key(purpose, ident)) or 0) >= MAX_SENDS_PER_HOUR:
        raise TooSoon(HOUR_SECONDS)


def _send(email, code):
    body = render_to_string('users/email_code_email.txt', {'code': code, 'minutes': LIFETIME_SECONDS // 60})
    try:
        send_mail(EMAIL_SUBJECT, body, None, [email])
    except Exception as error:  # SMTP errors are many kinds (refused, timeout, auth): all mean "not sent"
        raise SendFailed(type(error).__name__) from error


def issue(purpose, ident, email, payload=None, keep_payload_of=None):
    """
    Make a new code for `ident`, keep its hash, mail it to `email`. Raises TooSoon or SendFailed; a failed mail leaves
    nothing waiting. `keep_payload_of`: reuse the waiting data of an earlier code (a resend) instead of `payload`.
    """
    _check_may_send(purpose, ident)
    if keep_payload_of is not None:
        earlier = cache.get(entry_key(purpose, keep_payload_of))
        if earlier is None:
            raise LookupError('nothing waiting')
        payload = earlier['payload']
    code = new_code()
    now = _now()
    cache.set(entry_key(purpose, ident), {
        'digest': _digest(purpose, ident, code), 'sent_at': now, 'expires_at': now + LIFETIME_SECONDS,
        'payload': payload,
    }, LIFETIME_SECONDS)
    cache.delete(_tries_key(purpose, ident))
    try:
        _send(email, code)
    except SendFailed:
        cache.delete(entry_key(purpose, ident))
        raise
    _count_send(purpose, ident)


def waiting(purpose, ident):
    """True while a code for `ident` has been issued and has not expired or been used up."""
    entry = cache.get(entry_key(purpose, ident))
    return entry is not None and entry['expires_at'] > _now()


def verify(purpose, ident, code):
    """
    The data kept with the code ({} when none) if `code` is the live code of `ident`, else None. A right code is
    used up. Wrong tries are counted atomically; the fifth burns the code.
    """
    key = entry_key(purpose, ident)
    entry = cache.get(key)
    if entry is None or entry['expires_at'] <= _now() or not looks_like_a_code(code):
        return None
    tries_key = _tries_key(purpose, ident)
    cache.add(tries_key, 0, LIFETIME_SECONDS)
    try:
        tries = cache.incr(tries_key)
    except ValueError:
        tries = 1
        cache.set(tries_key, 1, LIFETIME_SECONDS)
    if tries > MAX_ATTEMPTS:
        cache.delete(key)
        return None
    if not hmac.compare_digest(entry['digest'], _digest(purpose, ident, code)):
        if tries >= MAX_ATTEMPTS:
            cache.delete(key)
        return None
    cache.delete(key)
    cache.delete(tries_key)
    return entry['payload'] or {}


def needs_code_at_login(user):
    """Guests and hotel owners: staff have the authenticator app (users.two_factor) and are never asked for this."""
    return settings.EMAIL_LOGIN_CODE_REQUIRED and not (user.is_staff or user.is_superuser or user.two_factor_enabled)


def remember_login_step(request, user):
    request.session[LOGIN_PENDING_KEY] = {'user': user.pk, 'at': _now()}


def forget_login_step(request):
    request.session.pop(LOGIN_PENDING_KEY, None)


def pending_login_user_id(request):
    pending = request.session.get(LOGIN_PENDING_KEY)
    if not pending or _now() - pending['at'] > LIFETIME_SECONDS:
        return None
    return pending['user']
