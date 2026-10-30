"""
Two-step sign-in: a code from an authenticator app (TOTP, RFC 6238) or a one-time backup code.

The app's secret is stored sealed (Fernet) so a leaked database alone is no use; backup codes are stored
only as hashes. The password step and the code step are two requests: the first leaves a short-lived note
in the session, the second turns it into a sign-in (users/views/two_factor.py).
"""
import hashlib
import json
import secrets
import time
from base64 import urlsafe_b64encode

import pyotp
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.models import Session
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

from users.models import User

ISSUER = 'TICKBRON'
STEP_SECONDS = 30
CODE_DIGITS = 6
BACKUP_CODE_COUNT = 10
PENDING_SECONDS = 5 * 60
PENDING_KEY = 'two_factor_pending'
SETUP_KEY = 'two_factor_setup_secret'


def _now():
    return time.time()


def needs_setup(user):
    """An administrator or staff member who must have two-step sign-in and has not set it up yet."""
    return bool(
        settings.TWO_FACTOR_REQUIRED_FOR_ADMINS and (user.is_staff or user.is_superuser) and not user.two_factor_enabled
    )


def _fernet():
    key = settings.TWO_FACTOR_KEY
    if not key:  # development and tests only: production refuses to start without TWO_FACTOR_KEY
        key = urlsafe_b64encode(hashlib.sha256(f'two-factor:{settings.SECRET_KEY}'.encode()).digest())
    return Fernet(key)


def seal(secret):
    return _fernet().encrypt(secret.encode()).decode()


def unseal(token):
    return _fernet().decrypt(token.encode()).decode()


def new_secret():
    return pyotp.random_base32()


def provisioning_uri(secret, email):
    """The otpauth:// link an authenticator app reads from the QR code."""
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)


def matching_step(secret, code, now=None):
    """The 30 second step the code belongs to (this one or one either side, for a slow phone clock), else None."""
    code = (code or '').replace(' ', '')
    if len(code) != CODE_DIGITS or not code.isdigit():
        return None
    totp = pyotp.TOTP(secret, digits=CODE_DIGITS, interval=STEP_SECONDS)
    current = int((_now() if now is None else now) // STEP_SECONDS)
    matches = [step for step in (current, current - 1, current + 1)
               if constant_time_compare(totp.at(step * STEP_SECONDS), code)]
    return matches[0] if matches else None


def accept_code(user, code):
    """True if the code is right and newer than the last one used; it then cannot be used again."""
    step = matching_step(unseal(user.two_factor_secret), code)
    if step is None:
        return False
    # The check and the write are one statement, so two requests carrying one code cannot both pass
    unused = Q(two_factor_last_step__isnull=True) | Q(two_factor_last_step__lt=step)
    return User.objects.filter(unused, pk=user.pk).update(two_factor_last_step=step) == 1


def _backup_hash(code):
    # Backup codes are random, so a fast keyed hash is enough (no one can guess them offline)
    clean = (code or '').strip().lower().replace('-', '').replace(' ', '')
    return salted_hmac('two-factor-backup-code', clean, algorithm='sha256').hexdigest()


def use_backup_code(user, code):
    """True if the code is one of the user's unused backup codes; it is then used up."""
    digest = _backup_hash(code)
    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=user.pk)
        hashes = json.loads(locked.two_factor_backup_codes or '[]')
        match = next((stored for stored in hashes if constant_time_compare(stored, digest)), None)
        if match is None:
            return False
        hashes.remove(match)
        locked.two_factor_backup_codes = json.dumps(hashes)
        locked.save(update_fields=['two_factor_backup_codes'])
    return True


def enable(user, secret, step):
    """Switch two-step sign-in on and return the backup codes (shown once, never stored in the clear)."""
    codes = [secrets.token_hex(5) for _ in range(BACKUP_CODE_COUNT)]
    user.two_factor_secret = seal(secret)
    user.two_factor_enabled = True
    user.two_factor_last_step = step
    user.two_factor_backup_codes = json.dumps([_backup_hash(code) for code in codes])
    user.save(update_fields=['two_factor_secret', 'two_factor_enabled', 'two_factor_last_step', 'two_factor_backup_codes'])
    return [f'{code[:5]}-{code[5:]}' for code in codes]


def end_sessions(user, keep_key=None):
    """Sign the user out everywhere (except the session `keep_key`, if given); sessions are rows in the database."""
    sessions = Session.objects.filter(expire_date__gt=timezone.now())
    if keep_key:
        sessions = sessions.exclude(session_key=keep_key)
    for session in sessions.iterator():
        if session.get_decoded().get(SESSION_KEY) == str(user.pk):
            session.delete()


def reset(user):
    """Switch two-step sign-in off and forget the secret and backup codes (a lost phone); the user is signed out everywhere."""
    user.two_factor_enabled = False
    user.two_factor_secret = None
    user.two_factor_backup_codes = None
    user.two_factor_last_step = None
    user.save(update_fields=['two_factor_enabled', 'two_factor_secret', 'two_factor_backup_codes', 'two_factor_last_step'])
    end_sessions(user)


def remember_password_step(request, user):
    request.session[PENDING_KEY] = {'user': user.pk, 'at': _now()}


def forget_password_step(request):
    request.session.pop(PENDING_KEY, None)


def pending_user(request):
    """The user whose password was accepted in the last 5 minutes on this session, or None."""
    pending = request.session.get(PENDING_KEY)
    if not pending or _now() - pending['at'] > PENDING_SECONDS:
        return None
    return User.objects.filter(pk=pending['user'], is_active=True).first()
